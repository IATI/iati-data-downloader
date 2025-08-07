import pytest
from azure.storage.blob import BlobServiceClient
from dotenv import dotenv_values

from src.context import get_app_version


@pytest.fixture
def get_and_clear_up_context():
    context = dotenv_values("tests/test-environment/.env")
    context["APP_VERSION"] = get_app_version()
    create_azure_blob_containers(context)
    yield context


def create_azure_blob_containers(context: dict):
    blob_service = BlobServiceClient.from_connection_string(context["IATI_CACHE_BLOB_STORAGE_CONNECTION_STRING"])

    containers = blob_service.list_containers()
    container_names = [c.name for c in containers]

    try:
        if context["IATI_CACHE_BLOB_STORAGE_CONTAINER_NAME"] not in container_names:
            blob_service.create_container(context["IATI_CACHE_BLOB_STORAGE_CONTAINER_NAME"])
            container_names.append(context["IATI_CACHE_BLOB_STORAGE_CONTAINER_NAME"])
    except Exception as e:
        context["logger"].error(
            "Could not create Azure blob storage container. "
            "Container name: {}. "
            "Error details: {}".format(
                context["IATI_CACHE_BLOB_STORAGE_CONTAINER_NAME"],
                e,
            )
        )
        raise e
    finally:
        blob_service.close()
