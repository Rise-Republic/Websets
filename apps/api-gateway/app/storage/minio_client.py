"""
MinIO S3 Python client with enforced server-side encryption
"""

import os
import boto3
from loguru import logger
from botocore.client import Config
from botocore.exceptions import ClientError
from app.config.env import read_secret

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = read_secret("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = read_secret("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "websets-data")
MINIO_CA_CERT = os.getenv("MINIO_CA_CERT")
MINIO_CLIENT_CERT = os.getenv("MINIO_CLIENT_CERT")
MINIO_CLIENT_KEY = os.getenv("MINIO_CLIENT_KEY")

extra_args = {}
if MINIO_CA_CERT:
    extra_args["verify"] = MINIO_CA_CERT
if MINIO_CLIENT_CERT and MINIO_CLIENT_KEY:
    extra_args["cert"] = (MINIO_CLIENT_CERT, MINIO_CLIENT_KEY)

s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
    **extra_args,
)


def tenant_object_name(tenant_id: str, object_name: str) -> str:
    """Return a key namespaced by tenant."""
    return f"{tenant_id}/{object_name}"


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
                ExtraArgs={"ServerSideEncryption": "AES256"},
            )
        logger.info(f"Uploaded {object_name} with AES256 encryption.")
    except ClientError as e:
        logger.error(f"Upload failed: {e}")
        raise


def download_file(file_name, dest_path):
    """Download file from MinIO."""
    try:
        with open(dest_path, "wb") as f:
            s3.download_fileobj(MINIO_BUCKET, file_name, f)
        logger.info(f"Downloaded {file_name} to {dest_path}.")
    except ClientError as e:
        logger.error(f"Download failed: {e}")
        raise
