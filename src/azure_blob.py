from typing import Any, Optional

import azure
from azure.storage.blob import BlobProperties, BlobServiceClient, ContentSettings

from src.data_downloader_exceptions import DatasetCacheError
from src.iati_utilities import get_dict_value_or_none, zip_data_as_single_file


def download_matches_cache(
    blob_service: BlobServiceClient, container: str, blob_base_name: str, download_length: int, download_hash: str
) -> tuple[bool, Optional[BlobProperties], Optional[BlobProperties]]:

    xml_blob_properties = get_azure_blob_properties(blob_service, container, blob_base_name + ".xml")
    zip_blob_properties = get_azure_blob_properties(blob_service, container, blob_base_name + ".zip")

    if (
        xml_blob_properties is not None
        and zip_blob_properties is not None
        and xml_blob_properties.size == download_length
        and xml_blob_properties.metadata.get("iati_hash", "no_hash") == download_hash
        and zip_blob_properties.metadata.get("iati_hash", "no_hash") == download_hash
    ):
        return (True, xml_blob_properties, zip_blob_properties)

    return (False, None, None)


def get_blob_name_from_dataset(dataset: dict, iati_blob_type: str) -> str:
    return "{}/{}.{}".format(dataset["reporting_org_short_name"], dataset["short_name"], iati_blob_type)


def get_azure_blob_properties(
    blob_service: BlobServiceClient, container: str, blob_name: str
) -> Optional[BlobProperties]:
    blob_client = blob_service.get_blob_client(container, blob_name)

    exists = blob_client.exists()

    if not exists:
        blob_client.close()
        return None

    blob_properties = blob_client.get_blob_properties()

    blob_client.close()

    return blob_properties


def upload_dataset_to_cache(
    context: dict, message_body: dict, content: Any, encoding: str | None, dataset_hash: str
) -> dict:

    dataset_download_cache_details = {}

    try:
        blob_service = BlobServiceClient.from_connection_string(context["IATI_CACHE_BLOB_STORAGE_CONNECTION_STRING"])

        container_name = context["IATI_CACHE_BLOB_STORAGE_CONTAINER_NAME"]

        xml_blob_name = get_blob_name_from_dataset(message_body["dataset"], "xml")

        zip_blob_name = get_blob_name_from_dataset(message_body["dataset"], "zip")

        dl_matches_cache, xml_blob_properties, zip_blob_properties = download_matches_cache(
            blob_service, container_name, xml_blob_name, len(content), dataset_hash
        )

        if dl_matches_cache:
            dataset_download_cache_details = {
                "cached_dataset_url_xml": "{}/{}".format(context["IATI_CACHE_BASE_URL"], xml_blob_name),
                "cached_dataset_url_zip": "{}/{}".format(context["IATI_CACHE_BASE_URL"], zip_blob_name),
                "cached_dataset_etag_xml": xml_blob_properties["etag"] if xml_blob_properties is not None else None,
                "cached_dataset_etag_zip": zip_blob_properties["etag"] if zip_blob_properties is not None else None,
            }
        else:
            # upload to our Azure blob storage cache only if content on Azure doesn't match download
            print(
                "Dataset ID {} - Cached copy of dataset in blob storage differs from download. "
                "Hash of download: {}. Uploading to cache.".format(message_body["dataset"]["id"], dataset_hash)
            )

            cache_of_xml_matches, xml_blob_details = upload_to_blob(
                blob_service,
                container_name,
                xml_blob_name,
                content,
                dataset_hash,
                "application/xml",
                encoding,
                retries=3,
            )

            cache_of_zip_matches, zip_blob_details = upload_to_blob(
                blob_service,
                container_name,
                zip_blob_name,
                zip_data_as_single_file(f"{message_body["dataset"]["short_name"]}.xml", content),
                dataset_hash,
                "application/zip",
                encoding,
                retries=3,
            )

            if cache_of_xml_matches and cache_of_zip_matches:
                dataset_download_cache_details = {
                    "cached_dataset_url_xml": "{}/{}".format(context["IATI_CACHE_BASE_URL"], xml_blob_name),
                    "cached_dataset_url_zip": "{}/{}".format(context["IATI_CACHE_BASE_URL"], zip_blob_name),
                    "cached_dataset_etag_xml": get_dict_value_or_none(xml_blob_details, "etag"),
                    "cached_dataset_etag_zip": get_dict_value_or_none(zip_blob_details, "etag"),
                }
            else:
                dataset_download_cache_details = {
                    "cached_dataset_url_xml": None,
                    "cached_dataset_url_zip": None,
                    "cached_dataset_etag_xml": None,
                    "cached_dataset_etag_zip": None,
                }

    except azure.core.exceptions.ServiceRequestError as e:
        raise DatasetCacheError(e)

    finally:
        if blob_service is not None:
            blob_service.close()

    return dataset_download_cache_details


def upload_to_blob(
    blob_service_client: BlobServiceClient,
    container_name: str,
    blob_name: str,
    content: Any,
    hash: str,
    content_type: str,
    encoding: str | None = None,
    retries: int = 3,
) -> tuple[bool, Optional[dict[str, Any]]]:

    blob_details = None
    blob_size_and_hash_match = False

    for attempt in range(retries):

        blob_client = blob_service_client.get_blob_client(container_name, blob_name)

        content_settings = ContentSettings(content_type=content_type)

        if content_type == "application/xml":
            content_settings.content_encoding = encoding

        blob_details = blob_client.upload_blob(
            content, overwrite=True, content_settings=content_settings, metadata={"iati_hash": hash}
        )

        blob_client.close()

        blob_size_and_hash_match, _ = verify_blob_upload(
            blob_service_client, container_name, blob_name, len(content), hash
        )

        if blob_size_and_hash_match:
            break

    return (blob_size_and_hash_match, blob_details)


def verify_blob_upload(
    blob_service: BlobServiceClient, container: str, blob_name: str, content_length: int, hash: str
) -> tuple[bool, Optional[BlobProperties]]:

    blob_properties = get_azure_blob_properties(blob_service, container, blob_name)

    if (
        blob_properties is not None
        and blob_properties.size == content_length
        and blob_properties.metadata.get("iati_hash", "no_hash") == hash
    ):
        return (True, blob_properties)

    return (False, None)
