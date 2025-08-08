from .iati_utilities import get_utc_timestamp_str_with_tz


def generate_download_attempt_result(
    message: dict,
    download_attempt_datetime: str,
    http_status: int | None,
    dataset_download_details: dict,
    error_details: dict,
) -> dict:

    return {
        "message_type": "DATASET_DOWNLOAD_ATTEMPT_RESULT",
        "message_date": get_utc_timestamp_str_with_tz(),
        "dataset_download_attempt_result": {
            "id": message["dataset"]["id"],
            "short_name": message["dataset"]["short_name"],
            "dataset_download_details": dataset_download_details,
            "get_attempt_result": {
                "datetime": download_attempt_datetime,
                "error_details": error_details,
                "error_occurred": True if dataset_download_details["hash"] is None else False,
                "http_status": http_status,
            },
        },
    }


def get_blank_dataset_download_details() -> dict:
    return {
        "cached_dataset_url_xml": None,
        "cached_dataset_url_zip": None,
        "cached_dataset_etag_xml": None,
        "cached_dataset_etag_zip": None,
        "content_length": None,
        "downloaded": None,
        "hash": None,
        "hash_excluding_generated_timestamp": None,
        "initial_contents": None,
        "server_header_etag": None,
        "server_header_last_modified": None,
        "source_url": None,
        "verified_on_server": None,
    }
