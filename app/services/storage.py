import abc
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Base exception for storage service operations."""
    pass


class BaseStorageService(abc.ABC):
    """Abstract base class defining the interface for decoupled file storage.
    
    Any storage provider (Supabase, S3, Local) must implement these methods.
    """

    @abc.abstractmethod
    async def upload_file(
        self,
        bucket: str,
        file_bytes: bytes,
        destination_path: str,
        content_type: str
    ) -> str:
        """Uploads a file to storage and returns its storage key.

        Args:
            bucket (str): The storage bucket/container name.
            file_bytes (bytes): The raw binary content of the file.
            destination_path (str): The path/filename inside the bucket.
            content_type (str): The MIME type of the file.

        Returns:
            str: The unique storage key/path of the uploaded file.
        """
        pass

    @abc.abstractmethod
    async def download_file(self, bucket: str, storage_key: str) -> bytes:
        """Downloads a file from storage as bytes.

        Args:
            bucket (str): The storage bucket name.
            storage_key (str): The storage key/path of the file.

        Returns:
            bytes: The file contents.
        """
        pass

    @abc.abstractmethod
    async def delete_file(self, bucket: str, storage_key: str) -> bool:
        """Deletes a file from storage.

        Args:
            bucket (str): The storage bucket name.
            storage_key (str): The storage key/path of the file.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        pass

    @abc.abstractmethod
    async def get_presigned_url(
        self,
        bucket: str,
        storage_key: str,
        expires_in: int = 3600
    ) -> str:
        """Generates a temporary signed URL for a private file.

        Args:
            bucket (str): The storage bucket name.
            storage_key (str): The storage key/path of the file.
            expires_in (int): Expiration time in seconds (default: 3600).

        Returns:
            str: The signed URL.
        """
        pass


class SupabaseStorageService(BaseStorageService):
    """Supabase Storage implementation using HTTP REST client."""

    def __init__(self) -> None:
        self.supabase_url = settings.SUPABASE_URL.rstrip("/")
        self.supabase_key = settings.SUPABASE_ANON_KEY
        self.base_url = f"{self.supabase_url}/storage/v1"
        self.headers = {
            "Authorization": f"Bearer {self.supabase_key}",
            "apikey": self.supabase_key,
        }

    async def upload_file(
        self,
        bucket: str,
        file_bytes: bytes,
        destination_path: str,
        content_type: str
    ) -> str:
        url = f"{self.base_url}/object/{bucket}/{destination_path.lstrip('/')}"
        headers = {**self.headers, "Content-Type": content_type}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, content=file_bytes, headers=headers)
                if response.status_code != 200:
                    logger.error(
                        f"Supabase upload failed: {response.status_code} - {response.text}"
                    )
                    raise StorageError(f"Failed to upload file: {response.text}")
                
                # Supabase returns {"Key": "bucket/path"} or similar
                data = response.json()
                return data.get("Key") or f"{bucket}/{destination_path}"
            except httpx.HTTPError as e:
                logger.exception("HTTP error during Supabase upload")
                raise StorageError(f"HTTP transport failure: {str(e)}")

    async def download_file(self, bucket: str, storage_key: str) -> bytes:
        # Strip bucket name from storage_key if it's prefixed
        path = storage_key
        prefix = f"{bucket}/"
        if path.startswith(prefix):
            path = path[len(prefix):]

        url = f"{self.base_url}/object/authenticated/{bucket}/{path.lstrip('/')}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers)
                if response.status_code != 200:
                    logger.error(
                        f"Supabase download failed: {response.status_code} - {response.text}"
                    )
                    raise StorageError(f"Failed to download file: {response.text}")
                return response.content
            except httpx.HTTPError as e:
                logger.exception("HTTP error during Supabase download")
                raise StorageError(f"HTTP transport failure: {str(e)}")

    async def delete_file(self, bucket: str, storage_key: str) -> bool:
        path = storage_key
        prefix = f"{bucket}/"
        if path.startswith(prefix):
            path = path[len(prefix):]

        url = f"{self.base_url}/object/{bucket}"

        async with httpx.AsyncClient() as client:
            try:
                # Supabase Storage bulk delete endpoint accepts a list of prefixes (files)
                response = await client.request(
                    "DELETE",
                    url,
                    json={"prefixes": [path.lstrip('/')]},
                    headers=self.headers
                )
                if response.status_code != 200:
                    logger.error(
                        f"Supabase delete failed: {response.status_code} - {response.text}"
                    )
                    return False
                return True
            except httpx.HTTPError:
                logger.exception("HTTP error during Supabase delete")
                return False

    async def get_presigned_url(
        self,
        bucket: str,
        storage_key: str,
        expires_in: int = 3600
    ) -> str:
        path = storage_key
        prefix = f"{bucket}/"
        if path.startswith(prefix):
            path = path[len(prefix):]

        url = f"{self.base_url}/object/sign/{bucket}/{path.lstrip('/')}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    json={"expiresIn": expires_in},
                    headers=self.headers
                )
                if response.status_code != 200:
                    logger.error(
                        f"Supabase sign URL failed: {response.status_code} - {response.text}"
                    )
                    raise StorageError(f"Failed to sign URL: {response.text}")
                
                data = response.json()
                # Supabase API usually returns {"signedURL": "..."} or {"signedUrl": "..."}
                signed_url = data.get("signedURL") or data.get("signedUrl")
                if not signed_url:
                    raise StorageError("Response missing signed URL key")
                
                # If Supabase returns relative URL, join with base URL
                if signed_url.startswith("/"):
                    signed_url = f"{self.supabase_url}{signed_url}"
                return signed_url
            except httpx.HTTPError as e:
                logger.exception("HTTP error during Supabase sign URL")
                raise StorageError(f"HTTP transport failure: {str(e)}")


# Singleton instance or helper dependency
def get_storage_service() -> BaseStorageService:
    """Dependency provider for storage service.
    
    Can be easily configured to return different implementations (S3, local, etc.).
    """
    return SupabaseStorageService()
