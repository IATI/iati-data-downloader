import datetime
import hashlib
import io
import re
import zipfile
from typing import Any

START_OF_IATI_XML_REGEX = re.compile(
    r"^(<\?xml[^>]*>)?\s*(<!--[^>]*-->\s*)*\s*<iati-(activities|organisations)", re.IGNORECASE
)


def content_has_iati_opening_element(content: str) -> bool:
    return START_OF_IATI_XML_REGEX.search(content) is not None


def get_dict_value_or_none(d: dict | None, k: str) -> Any:
    if d is None or not isinstance(d, dict):
        return None
    return d.get(k, None)


def get_hash_of_bytes(content: bytes) -> str:
    hasher = hashlib.sha1()
    hasher.update(content)
    return hasher.hexdigest()


def get_hash_excluding_generated_timestamp(content: str, encoding: str) -> str:
    content_to_hash = re.sub(r'generated-datetime="[^"]+"', "", content)
    hasher = hashlib.sha1()
    hasher.update(content_to_hash.encode(encoding))
    return hasher.hexdigest()


def get_utc_timestamp_str_with_tz(timestamp: datetime.datetime | None = None) -> str:
    if timestamp is not None:
        return timestamp.isoformat()
    else:
        return datetime.datetime.now(tz=datetime.timezone.utc).replace(microsecond=0).isoformat()


def zip_data_as_single_file(filename: str, data: bytes) -> bytes:

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as xml_zipped:
        xml_zipped.writestr(filename, data)

    return zip_buffer.getvalue()
