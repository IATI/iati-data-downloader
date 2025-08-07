import datetime
from typing import Any, Optional  # noqa

import chardet
import requests
from urllib3.util import Retry

from .data_downloader_exceptions import DatasetDownloadError
from .iati_utilities import content_has_iati_opening_element


def determine_response_encoding(download_response: requests.Response) -> str | None:
    detection_result = chardet.detect(download_response.content)
    return detection_result["encoding"]


def http_download_dataset(session: requests.Session, url: str, timeout: int = 25) -> requests.Response:

    response = None

    try:
        response = session.get(url=url, timeout=timeout, allow_redirects=True)

    except requests.exceptions.ConnectionError as e:
        error_args = get_http_get_attempt_error_details(
            "connection_error", "Download attempt failed with a connection error", url, response, e
        )

        raise DatasetDownloadError(error_args)

    except requests.exceptions.ConnectTimeout as e:
        error_args = get_http_get_attempt_error_details(
            "connection_timeout", "Download attempt failed due to connection timeout", url, response, e
        )

        raise DatasetDownloadError(error_args)

    except requests.exceptions.SSLError as e:
        error_args = get_http_get_attempt_error_details(
            "ssl_error", "Download attempt failed due to SSL error", url, response, e
        )

        raise DatasetDownloadError(error_args)

    if response.status_code == 404:
        error_args = get_http_get_attempt_error_details(
            "http_404_not_found", "Dataset was not found on source server", url, response, None
        )
        raise DatasetDownloadError(error_args)

    if response.status_code != 200:
        error_args = get_http_get_attempt_error_details(
            "http_non_200", "Download attempt failed with a non-200 HTTP status", url, response, None
        )
        raise DatasetDownloadError(error_args)

    return response


def get_http_get_attempt_error_details(
    error_type: str, summary: str, url: str, resp: requests.Response | None, e: Exception | None
) -> dict:
    error_details = {
        "error_type": error_type,
        "http_method": "GET",
        "http_reason": None,
        "http_status": None,
        "http_headers": {},
        "summary_message": summary,
        "system_message": "{}".format(e) if e is not None else None,
        "url": url,
    }  # type: dict[str, Any]

    if resp is not None:
        error_details["http_status"] = resp.status_code
        error_details["http_reason"] = resp.reason
        error_details["http_headers"] = dict(resp.headers)

    return error_details


def get_initial_chars_if_text(http_response: requests.Response, encoding: str | None) -> str | None:
    if encoding is None:
        return None

    http_response.encoding = encoding

    return http_response.text[:6000].replace("\n", "").replace("\r", "")


def get_initial_iati_content(http_response: requests.Response, encoding: str | None) -> str:

    initial_chars = get_initial_chars_if_text(http_response, encoding)

    if initial_chars is None:
        error_args = get_http_get_attempt_error_details(
            "not_iati_content", "Download is not an IATI document", http_response.url, http_response, None
        )
        raise DatasetDownloadError(error_args)

    initial_chars_wo_newlines = initial_chars.replace("\n", "").replace("\r", "")

    if not content_has_iati_opening_element(initial_chars_wo_newlines):
        error_args = get_http_get_attempt_error_details(
            "not_iati_content", "Download is not an IATI document", http_response.url, http_response, None
        )
        raise DatasetDownloadError(error_args)

    return initial_chars_wo_newlines[:150]


def get_last_modified_header_if_exists(download_response: requests.Response) -> Optional[datetime.datetime]:
    last_modified_header = None
    if download_response.headers.get("Last-Modified", None) is not None:
        last_modified_header = parse_last_modified_header(download_response.headers.get("Last-Modified", ""))
    return last_modified_header


def get_requests_session(context: dict) -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "IATI Data Downloader {}".format(context["APP_VERSION"])})
    retries = Retry(total=2, backoff_factor=0.1)
    session.mount("http://", requests.adapters.HTTPAdapter(max_retries=retries))
    session.mount("https://", requests.adapters.HTTPAdapter(max_retries=retries))
    return session


def parse_last_modified_header(last_modified_header: str) -> Optional[datetime.datetime]:
    last_modified_header_parsed = None
    try:
        last_modified_header_parsed = datetime.datetime.strptime(
            last_modified_header, "%a, %d %b %Y %H:%M:%S %Z"
        ).replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        pass
    return last_modified_header_parsed
