from azure.storage.blob import BlobServiceClient


def delete_blob(blob_service: BlobServiceClient, container_name: str, blob_name: str):
    try:
        blob_client = blob_service.get_blob_client(container_name, blob_name)
        if blob_client.exists():
            blob_client.delete_blob()
    finally:
        blob_client.close()


def download_blob(blob_service: BlobServiceClient, container_name: str, blob_name: str) -> bytes | None:
    content = None
    try:
        blob_client = blob_service.get_blob_client(container_name, blob_name)
        if blob_client.exists():
            content = blob_client.download_blob().readall()
    finally:
        blob_client.close()
    return content
