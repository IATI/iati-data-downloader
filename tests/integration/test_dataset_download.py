import pytest

from function_app import download_and_cache_dataset
from helpers.context import get_and_clear_up_context  # noqa: F401


@pytest.mark.parametrize(
    "http_status",
    [
        (400),
        (401),
        (403),
        (404),
        (500),
    ],
)
def test_download_http_errors_reported_correctly(get_and_clear_up_context, http_status: int):  # noqa: F811

    context = get_and_clear_up_context

    message_body = {
        "message_type": "DATASET_DOWNLOAD_REQUEST",
        "message_date": "2025-06-27T06:54:20+00:00",
        "dataset": {
            "id": "5401c7f4-e9fd-4ce3-b184-bfe1cb71a9f8",
            "short_name": "aidagcy-activity-3",
            "source_type": "primary-source",
            "licence_id": "gpl-3.0",
            "url": f"http://localhost:3005/error-response/{http_status}",
            "last_url_update_date": "2025-06-27T06:54:20+00:00",
            "last_metadata_update_date": "2025-06-27T06:54:20+00:00",
            "reporting_org_id": "cc66ce2a-ff59-4cc8-9e2e-0424fb12ae10",
            "reporting_org_short_name": "aidagcy",
        },
        "dataset_hash_details": {
            "hash": "041c7dba17b9356be78edc99016d337aa7c33f3a",
            "hash_excluding_generated_timestamp": "738a1ad14dca2451fa89e642b753101dcf57ce2f",
        },
    }

    result = download_and_cache_dataset(context, message_body)

    for k in result["dataset_download_attempt_result"]["dataset_download_details"].keys():
        assert result["dataset_download_attempt_result"]["dataset_download_details"][k] is None

    assert result["dataset_download_attempt_result"]["get_attempt_result"]["error_occurred"] is True
    assert result["dataset_download_attempt_result"]["get_attempt_result"]["http_status"] == http_status
    assert (
        result["dataset_download_attempt_result"]["get_attempt_result"]["error_details"]["http_status"] == http_status
    )


def test_download_success(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    message_body = {
        "message_type": "DATASET_DOWNLOAD_REQUEST",
        "message_date": "2025-06-27T06:54:20+00:00",
        "dataset": {
            "id": "5401c7f4-e9fd-4ce3-b184-bfe1cb71a9f8",
            "short_name": "aidagcy-activity-3",
            "source_type": "primary-source",
            "licence_id": "gpl-3.0",
            "url": "http://localhost:3005/datasets/activity_file_01.xml",
            "last_url_update_date": "2025-06-27T06:54:20+00:00",
            "last_metadata_update_date": "2025-06-27T06:54:20+00:00",
            "reporting_org_id": "cc66ce2a-ff59-4cc8-9e2e-0424fb12ae10",
            "reporting_org_short_name": "aidagcy",
        },
        "dataset_hash_details": {
            "hash": "041c7dba17b9356be78edc99016d337aa7c33f3a",
            "hash_excluding_generated_timestamp": "738a1ad14dca2451fa89e642b753101dcf57ce2f",
        },
    }

    result = download_and_cache_dataset(context, message_body)

    for k in result["dataset_download_attempt_result"]["dataset_download_details"].keys():
        assert result["dataset_download_attempt_result"]["dataset_download_details"][k] is not None, f"key: {k}"

    assert result["dataset_download_attempt_result"]["get_attempt_result"]["error_occurred"] is False
    assert result["dataset_download_attempt_result"]["get_attempt_result"]["error_details"] == {}
