"""
MinIO S3 Python client with enforced server-side encryption
"""
import os
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "websets-data")

s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1"
)

def upload_file_encrypted(file_path, object_name=None):
    """Upload file to MinIO with server-side encryption (AES256)."""
    if object_name is None:
        object_name = os.path.basename(file_path)
    try:
        with open(file_path, "rb") as f:
            s3.upload_fileobj(
                f,
                MINIO_BUCKET,
                object_name,
                ExtraArgs={"ServerSideEncryption": "AES256"}
            )
        print(f"Uploaded {object_name} with AES256 encryption.")
    except ClientError as e:
        print(f"Upload failed: {e}")
        raise

def download_file(file_name, dest_path):
    """Download file from MinIO."""
    try:
        with open(dest_path, "wb") as f:
            s3.download_fileobj(MINIO_BUCKET, file_name, f)
        print(f"Downloaded {file_name} to {dest_path}.")
    except ClientError as e:
        print(f"Download failed: {e}")
        raise
