import os
from pathlib import Path

import toml


def get_app_version() -> str:
    app_version = "Unknown Version"
    pyproject_file = Path(__file__).parent.parent / "pyproject.toml"
    if pyproject_file.exists():
        pyproject_data = toml.load(pyproject_file)
        if "project" in pyproject_data and "version" in pyproject_data["project"]:
            app_version = pyproject_data["project"]["version"]
    return app_version


def get_context() -> dict:
    return {
        "APP_VERSION": get_app_version(),
        "IATI_CACHE_BLOB_STORAGE_CONNECTION_STRING": os.getenv("IATI_CACHE_BLOB_STORAGE_CONNECTION_STRING", ""),
        "IATI_CACHE_BLOB_STORAGE_CONTAINER_NAME": os.getenv("IATI_CACHE_BLOB_STORAGE_CONTAINER_NAME", ""),
        "IATI_CACHE_BASE_URL": os.getenv("IATI_CACHE_BASE_URL", ""),
    }
