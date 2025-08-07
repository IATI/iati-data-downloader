import uuid

import chardet
import pytest
from azure.storage.blob import BlobServiceClient, ContentSettings

from helpers.azure import delete_blob, download_blob
from helpers.context import get_and_clear_up_context  # noqa: F401
from src.azure_blob import upload_dataset_to_cache, verify_blob_upload
from src.iati_utilities import zip_data_as_single_file


@pytest.mark.parametrize(
    "filename",
    [
        ("tests/artefacts/dataset-files/test_foundation_a-dataset-001-iso-8859-1"),
        ("tests/artefacts/dataset-files/test_foundation_a-dataset-001-utf-8"),
        ("tests/artefacts/dataset-files/test_foundation_a-dataset-001-utf-8-with-bom"),
        ("tests/artefacts/dataset-files/test_foundation_a-dataset-001-utf-16-be"),
        ("tests/artefacts/dataset-files/test_foundation_a-dataset-001-utf-16-le"),
        ("tests/artefacts/dataset-files/test_foundation_a-dataset-001-utf-32-be"),
        ("tests/artefacts/dataset-files/test_foundation_a-dataset-001-utf-32-le"),
    ],
)
def test_blob_upload(get_and_clear_up_context, filename):  # noqa: F811
    context = get_and_clear_up_context

    try:
        blob_service = BlobServiceClient.from_connection_string(context["IATI_CACHE_BLOB_STORAGE_CONNECTION_STRING"])

        message_body = {
            "dataset": {"id": uuid.uuid4(), "short_name": "dataset-a", "reporting_org_short_name": "org-a"}
        }

        with open(filename, "rb") as f:
            dataset_content = f.read()

        encoding = chardet.detect(dataset_content)

        upload_details = upload_dataset_to_cache(context, message_body, dataset_content, encoding, "test-hash")

        assert upload_details["cached_dataset_url_xml"].endswith("org-a/dataset-a.xml")
        assert upload_details["cached_dataset_url_zip"].endswith("org-a/dataset-a.zip")
        assert upload_details["cached_dataset_etag_xml"] is not None
        assert upload_details["cached_dataset_etag_zip"] is not None

        xml = download_blob(blob_service, context["IATI_CACHE_BLOB_STORAGE_CONTAINER_NAME"], "org-a/dataset-a.xml")

        assert xml == dataset_content

        zipfile = download_blob(blob_service, context["IATI_CACHE_BLOB_STORAGE_CONTAINER_NAME"], "org-a/dataset-a.zip")

        zip_content = zip_data_as_single_file("dataset-a.xml", dataset_content)

        assert zipfile == zip_content

    finally:
        delete_blob(blob_service, context["IATI_CACHE_BLOB_STORAGE_CONTAINER_NAME"], "org-a/dataset-a.xml")
        delete_blob(blob_service, context["IATI_CACHE_BLOB_STORAGE_CONTAINER_NAME"], "org-a/dataset-a.zip")
        blob_service.close()


@pytest.mark.parametrize(
    "filename",
    [
        ("tests/artefacts/dataset-files/test_foundation_a-dataset-001-iso-8859-1"),
        ("tests/artefacts/dataset-files/test_foundation_a-dataset-001-utf-8"),
        ("tests/artefacts/dataset-files/test_foundation_a-dataset-001-utf-8-with-bom"),
        ("tests/artefacts/dataset-files/test_foundation_a-dataset-001-utf-16-be"),
        ("tests/artefacts/dataset-files/test_foundation_a-dataset-001-utf-16-le"),
        ("tests/artefacts/dataset-files/test_foundation_a-dataset-001-utf-32-be"),
        ("tests/artefacts/dataset-files/test_foundation_a-dataset-001-utf-32-le"),
    ],
)
def test_blob_upload_verification(get_and_clear_up_context, filename):  # noqa: F811
    context = get_and_clear_up_context

    try:
        with open(filename, "rb") as f:
            content = f.read()

        # manually upload blob, not using Data Downloader code
        blob_service = BlobServiceClient.from_connection_string(context["IATI_CACHE_BLOB_STORAGE_CONNECTION_STRING"])
        container = context["IATI_CACHE_BLOB_STORAGE_CONTAINER_NAME"]
        blob_name = "org-a/dataset-a.xml"
        blob_client = blob_service.get_blob_client(container, blob_name)
        content_settings = ContentSettings(content_type="application/xml")
        content_settings.content_encoding = chardet.detect(content)
        blob_client.upload_blob(content, content_settings=content_settings, metadata={"iati_hash": "test-hash"})

        # the function under test
        ok, blob_details = verify_blob_upload(blob_service, container, blob_name, len(content), "test-hash")

        assert ok
        assert blob_details.size == len(content)
        assert blob_details.metadata.get("iati_hash") == "test-hash"

    finally:
        blob_client.delete_blob()
        blob_client.close()
        blob_service.close()
