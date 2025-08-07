import json
import os
import traceback

import azure.functions as func

from src.azure_blob import upload_dataset_to_cache
from src.context import get_context
from src.data_downloader_exceptions import DatasetCacheError, DatasetDownloadError
from src.http import (
    determine_response_encoding,
    get_initial_iati_content,
    get_last_modified_header_if_exists,
    get_requests_session,
    http_download_dataset,
)
from src.iati_utilities import (
    get_dict_value_or_none,
    get_hash_excluding_generated_timestamp,
    get_hash_of_bytes,
    get_utc_timestamp_str_with_tz,
)
from src.response_helpers import generate_download_attempt_result, get_blank_dataset_download_details

app = func.FunctionApp()


@app.service_bus_queue_trigger("msg", "MQS_CONNECTION_STRING", os.getenv("MQS_DOWNLOAD_REQUEST_QUEUE_NAME", ""))
@app.service_bus_topic_output(
    "output_msg", "MQS_CONNECTION_STRING", os.getenv("MQS_DOWNLOAD_ATTEMPT_RESULT_TOPIC_NAME", "")
)
def process_dataset_download_request(msg: func.ServiceBusMessage, output_msg: func.Out[str]):

    context = get_context()

    if msg.application_properties.get("message_type", "") == "DATASET_DOWNLOAD_REQUEST":
        try:
            message_body = json.loads(msg.get_body().decode("utf-8"))

            result = download_and_cache_dataset(context, message_body)

            output_msg.set(json.dumps(result, indent=2))

        except json.JSONDecodeError as e:
            print(f"ERROR: Message of type {msg.application_properties["message_type"]} not valid JSON")
            print(f"Details: {str(e)}")
        except Exception as e:
            print("ERROR: Unexpected error: {}".format(e))
            print(traceback.format_exc())
    else:
        if "message_type" in msg.application_properties:
            print(f"ERROR: Discarding message of type: {msg.application_properties["message_type"]}")
        else:
            print("ERROR: Discarding message without 'message_type' set")


def download_and_cache_dataset(context: dict, message_body: dict) -> dict:

    download_attempt_ts = get_utc_timestamp_str_with_tz()
    error_details = {}
    dataset_download_details = get_blank_dataset_download_details()
    http_response = None
    http_status = None

    try:
        # download
        with get_requests_session(context) as session:
            http_response = http_download_dataset(session, message_body["dataset"]["url"])

        http_status = http_response.status_code

        # work out if it is IATI
        encoding = determine_response_encoding(http_response)

        initial_iati_content = get_initial_iati_content(http_response, encoding)

        # get the hash
        dataset_hash = get_hash_of_bytes(http_response.content)

        hash_excluding_generated = get_hash_excluding_generated_timestamp(http_response.text, encoding)  # type: ignore

        dataset_download_details = dataset_download_details | {
            "content_length": len(http_response.content),
            "downloaded": download_attempt_ts,
            "hash": dataset_hash,
            "hash_excluding_generated_timestamp": hash_excluding_generated,
            "initial_contents": initial_iati_content,
            "server_header_etag": http_response.headers.get("ETag", None),
            "server_header_last_modified": get_utc_timestamp_str_with_tz(
                get_last_modified_header_if_exists(http_response)
            ),
            "source_url": message_body["dataset"]["url"],
            "verified_on_server": download_attempt_ts,
        }

        dataset_download_cache_details = upload_dataset_to_cache(
            context, message_body, http_response.content, encoding, dataset_hash
        )

        dataset_download_details = dataset_download_details | dataset_download_cache_details

    except DatasetDownloadError as e:
        error_details = e.args[0]
        http_status = get_dict_value_or_none(e.args[0], "http_status")

    except DatasetCacheError:
        print("Error communicating with IATI XML Azure Blob Storage Cache")
        print(traceback.format_exc())

    return generate_download_attempt_result(
        message_body, download_attempt_ts, http_status, dataset_download_details, error_details
    )
