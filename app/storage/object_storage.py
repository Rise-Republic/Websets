from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, BinaryIO, List
from pathlib import Path
from enum import Enum
import hashlib
import asyncio
from datetime import datetime
from loguru import logger

from app.config import settings


class ObjectStorageProvider(str, Enum):
    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"


class BaseObjectStorage(ABC):
    """Abstract base class for object storage implementations."""
    
    @abstractmethod
    async def upload_file(self, file_path: str, key: str, content_type: Optional[str] = None) -> str:
        """Upload a file and return the storage URL."""
        pass
    
    @abstractmethod
    async def upload_bytes(self, data: bytes, key: str, content_type: Optional[str] = None) -> str:
        """Upload bytes data and return the storage URL."""
        pass
    
    @abstractmethod
    async def download_file(self, key: str, local_path: str) -> bool:
        """Download a file to local path."""
        pass
    
    @abstractmethod
    async def delete_file(self, key: str) -> bool:
        """Delete a file."""
        pass
    
    @abstractmethod
    async def get_file_url(self, key: str, expires_in: int = 3600) -> str:
        """Get a signed URL for file access."""
        pass
    
    @abstractmethod
    async def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List files with optional prefix."""
        pass


class LocalObjectStorage(BaseObjectStorage):
    """Local filesystem storage implementation."""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or settings.data_dir)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, key: str) -> Path:
        """Get full file path for a key."""
        return self.base_path / key
    
    async def upload_file(self, file_path: str, key: str, content_type: Optional[str] = None) -> str:
        """Upload a file to local storage."""
        try:
            source_path = Path(file_path)
            dest_path = self._get_file_path(key)
            
            # Create directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            import shutil
            shutil.copy2(source_path, dest_path)
            
            logger.info(f"Uploaded file to local storage: {key}")
            return str(dest_path)
            
        except Exception as e:
            logger.error(f"Failed to upload file to local storage: {e}")
            raise
    
    async def upload_bytes(self, data: bytes, key: str, content_type: Optional[str] = None) -> str:
        """Upload bytes data to local storage."""
        try:
            file_path = self._get_file_path(key)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'wb') as f:
                f.write(data)
            
            logger.info(f"Uploaded bytes to local storage: {key}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to upload bytes to local storage: {e}")
            raise
    
    async def download_file(self, key: str, local_path: str) -> bool:
        """Download file from local storage."""
        try:
            source_path = self._get_file_path(key)
            if not source_path.exists():
                return False
            
            import shutil
            shutil.copy2(source_path, local_path)
            return True
            
        except Exception as e:
            logger.error(f"Failed to download file from local storage: {e}")
            return False
    
    async def delete_file(self, key: str) -> bool:
        """Delete file from local storage."""
        try:
            file_path = self._get_file_path(key)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete file from local storage: {e}")
            return False
    
    async def get_file_url(self, key: str, expires_in: int = 3600) -> str:
        """Get file URL for local storage."""
        file_path = self._get_file_path(key)
        if file_path.exists():
            return f"file://{file_path.absolute()}"
        raise FileNotFoundError(f"File not found: {key}")
    
    async def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List files in local storage."""
        try:
            files = []
            prefix_path = self.base_path / prefix if prefix else self.base_path
            
            if prefix_path.is_dir():
                for file_path in prefix_path.rglob("*"):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(self.base_path)
                        files.append({
                            "key": str(relative_path),
                            "size": file_path.stat().st_size,
                            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        })
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files in local storage: {e}")
            return []


class S3ObjectStorage(BaseObjectStorage):
    """AWS S3 storage implementation."""
    
    def __init__(self):
        self.bucket_name = settings.s3_bucket_name
        self.client = None
        self._initialize()
    
    def _initialize(self):
        """Initialize S3 client."""
        try:
            import boto3
            
            self.client = boto3.client(
                's3',
                region_name=settings.s3_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key
            )
            
            logger.info(f"Initialized S3 client for bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise
    
    async def upload_file(self, file_path: str, key: str, content_type: Optional[str] = None) -> str:
        """Upload file to S3."""
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            # Run S3 upload in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                self.client.upload_file,
                file_path, 
                self.bucket_name, 
                key,
                extra_args
            )
            
            url = f"s3://{self.bucket_name}/{key}"
            logger.info(f"Uploaded file to S3: {url}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to upload file to S3: {e}")
            raise
    
    async def upload_bytes(self, data: bytes, key: str, content_type: Optional[str] = None) -> str:
        """Upload bytes data to S3."""
        try:
            import io
            
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            # Run S3 upload in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.client.upload_fileobj,
                io.BytesIO(data),
                self.bucket_name,
                key,
                extra_args
            )
            
            url = f"s3://{self.bucket_name}/{key}"
            logger.info(f"Uploaded bytes to S3: {url}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to upload bytes to S3: {e}")
            raise
    
    async def download_file(self, key: str, local_path: str) -> bool:
        """Download file from S3."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.client.download_file,
                self.bucket_name,
                key,
                local_path
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to download file from S3: {e}")
            return False
    
    async def delete_file(self, key: str) -> bool:
        """Delete file from S3."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.client.delete_object,
                Bucket=self.bucket_name,
                Key=key
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file from S3: {e}")
            return False
    
    async def get_file_url(self, key: str, expires_in: int = 3600) -> str:
        """Get signed URL for S3 file."""
        try:
            loop = asyncio.get_event_loop()
            url = await loop.run_in_executor(
                None,
                self.client.generate_presigned_url,
                'get_object',
                {'Bucket': self.bucket_name, 'Key': key},
                expires_in
            )
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate S3 signed URL: {e}")
            raise
    
    async def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List files in S3."""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.client.list_objects_v2,
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    "key": obj['Key'],
                    "size": obj['Size'],
                    "modified": obj['LastModified'].isoformat()
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list S3 files: {e}")
            return []


class GCSObjectStorage(BaseObjectStorage):
    """Google Cloud Storage implementation."""
    
    def __init__(self):
        self.bucket_name = settings.gcs_bucket_name
        self.client = None
        self.bucket = None
        self._initialize()
    
    def _initialize(self):
        """Initialize GCS client."""
        try:
            from google.cloud import storage
            import os
            
            # Set credentials if provided
            if settings.gcs_credentials_path:
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.gcs_credentials_path
            
            self.client = storage.Client()
            self.bucket = self.client.bucket(self.bucket_name)
            
            logger.info(f"Initialized GCS client for bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            raise
    
    async def upload_file(self, file_path: str, key: str, content_type: Optional[str] = None) -> str:
        """Upload file to GCS."""
        try:
            blob = self.bucket.blob(key)
            
            # Set content type if provided
            if content_type:
                blob.content_type = content_type
            
            # Run upload in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                blob.upload_from_filename,
                file_path
            )
            
            url = f"gs://{self.bucket_name}/{key}"
            logger.info(f"Uploaded file to GCS: {url}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to upload file to GCS: {e}")
            raise
    
    async def upload_bytes(self, data: bytes, key: str, content_type: Optional[str] = None) -> str:
        """Upload bytes data to GCS."""
        try:
            blob = self.bucket.blob(key)
            
            if content_type:
                blob.content_type = content_type
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                blob.upload_from_string,
                data
            )
            
            url = f"gs://{self.bucket_name}/{key}"
            logger.info(f"Uploaded bytes to GCS: {url}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to upload bytes to GCS: {e}")
            raise
    
    async def download_file(self, key: str, local_path: str) -> bool:
        """Download file from GCS."""
        try:
            blob = self.bucket.blob(key)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                blob.download_to_filename,
                local_path
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to download file from GCS: {e}")
            return False
    
    async def delete_file(self, key: str) -> bool:
        """Delete file from GCS."""
        try:
            blob = self.bucket.blob(key)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, blob.delete)
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file from GCS: {e}")
            return False
    
    async def get_file_url(self, key: str, expires_in: int = 3600) -> str:
        """Get signed URL for GCS file."""
        try:
            from datetime import timedelta
            
            blob = self.bucket.blob(key)
            
            loop = asyncio.get_event_loop()
            url = await loop.run_in_executor(
                None,
                blob.generate_signed_url,
                expiration=timedelta(seconds=expires_in)
            )
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate GCS signed URL: {e}")
            raise
    
    async def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List files in GCS."""
        try:
            loop = asyncio.get_event_loop()
            blobs = await loop.run_in_executor(
                None,
                list,
                self.client.list_blobs(self.bucket_name, prefix=prefix)
            )
            
            files = []
            for blob in blobs:
                files.append({
                    "key": blob.name,
                    "size": blob.size,
                    "modified": blob.time_created.isoformat()
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list GCS files: {e}")
            return []


class ObjectStorageFactory:
    """Factory for creating object storage instances."""
    
    @staticmethod
    def create_storage(provider: ObjectStorageProvider) -> BaseObjectStorage:
        """Create an object storage instance."""
        if provider == ObjectStorageProvider.LOCAL:
            return LocalObjectStorage()
        elif provider == ObjectStorageProvider.S3:
            return S3ObjectStorage()
        elif provider == ObjectStorageProvider.GCS:
            return GCSObjectStorage()
        else:
            raise ValueError(f"Unsupported object storage provider: {provider}")


# Singleton instance
_storage_instance = None

def get_object_storage() -> BaseObjectStorage:
    """Get the configured object storage instance."""
    global _storage_instance
    
    if _storage_instance is None:
        provider = ObjectStorageProvider(settings.object_storage_provider)
        _storage_instance = ObjectStorageFactory.create_storage(provider)
    
    return _storage_instance