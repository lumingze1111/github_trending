"""Aliyun OSS uploader for file storage."""

from typing import Optional
from pathlib import Path
import oss2
from loguru import logger

from src.exceptions import OSSException
from src.utils import retry_on_exception


class OSSUploader:
    """Uploader for Aliyun OSS."""

    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        bucket_name: str,
        endpoint: str,
        path_prefix: str = "",
    ):
        """Initialize OSS uploader.

        Args:
            access_key_id: OSS access key ID
            access_key_secret: OSS access key secret
            bucket_name: OSS bucket name
            endpoint: OSS endpoint (e.g., "oss-cn-hangzhou.aliyuncs.com")
            path_prefix: Path prefix for uploaded files
        """
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.bucket_name = bucket_name
        self.endpoint = endpoint
        self.path_prefix = path_prefix.rstrip("/")

        try:
            auth = oss2.Auth(access_key_id, access_key_secret)
            self.bucket = oss2.Bucket(auth, endpoint, bucket_name)
            logger.info(f"OSS uploader initialized for bucket: {bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize OSS uploader: {e}")
            raise OSSException(f"Failed to initialize OSS: {e}")

    @retry_on_exception(max_retries=3, backoff=[1, 2, 4])
    def upload_file(self, local_path: str, object_name: Optional[str] = None) -> str:
        """Upload file to OSS.

        Args:
            local_path: Path to local file
            object_name: OSS object name (if None, uses filename from local_path)

        Returns:
            Public URL of the uploaded file

        Raises:
            OSSException: If upload fails
        """
        local_file = Path(local_path)
        if not local_file.exists():
            raise OSSException(f"Local file not found: {local_path}")

        # Determine object name
        if object_name is None:
            object_name = local_file.name

        # Add path prefix
        if self.path_prefix:
            object_name = f"{self.path_prefix}/{object_name}"

        try:
            # Upload file
            with open(local_path, "rb") as f:
                result = self.bucket.put_object(object_name, f)

            if result.status != 200:
                raise OSSException(f"Upload failed with status: {result.status}")

            # Set public read ACL
            self.bucket.put_object_acl(object_name, oss2.OBJECT_ACL_PUBLIC_READ)

            # Generate public URL
            url = self._generate_public_url(object_name)
            logger.info(f"File uploaded successfully: {url}")
            return url

        except oss2.exceptions.OssError as e:
            logger.error(f"OSS error during upload: {e}")
            raise OSSException(f"Failed to upload to OSS: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            raise OSSException(f"Failed to upload file: {e}")

    def _generate_public_url(self, object_name: str) -> str:
        """Generate public URL for an object.

        Args:
            object_name: OSS object name

        Returns:
            Public URL
        """
        # Format: https://{bucket}.{endpoint}/{object_name}
        return f"https://{self.bucket_name}.{self.endpoint}/{object_name}"

    def file_exists(self, object_name: str) -> bool:
        """Check if file exists in OSS.

        Args:
            object_name: OSS object name

        Returns:
            True if file exists, False otherwise
        """
        try:
            self.bucket.head_object(object_name)
            return True
        except oss2.exceptions.NoSuchKey:
            return False
        except Exception as e:
            logger.warning(f"Error checking file existence: {e}")
            return False

    def delete_file(self, object_name: str) -> bool:
        """Delete file from OSS.

        Args:
            object_name: OSS object name

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            self.bucket.delete_object(object_name)
            logger.info(f"File deleted: {object_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False
