import os
from loguru import logger

from app.secrets.vault import VaultClient
from .celery_app import celery_app

VAULT_PATH = os.getenv("MINIO_VAULT_PATH", "secret/websets")

@celery_app.task
def rotate_minio_credentials() -> bool:
    """Rotate MinIO credentials stored in Vault."""
    try:
        client = VaultClient()
        client.rotate_secret(VAULT_PATH, "MINIO_ACCESS_KEY", length=16)
        client.rotate_secret(VAULT_PATH, "MINIO_SECRET_KEY", length=32)
        logger.info("MinIO credentials rotated in Vault")
        return True
    except Exception as exc:
        logger.error(f"Failed to rotate MinIO credentials: {exc}")
        return False
