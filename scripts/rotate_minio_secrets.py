#!/usr/bin/env python3
"""Rotate MinIO credentials stored in Vault."""

import os
import sys
from loguru import logger
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.secrets.vault import VaultClient

DEFAULT_PATH = os.getenv("MINIO_VAULT_PATH", "secret/websets")


def rotate_minio() -> tuple[str, str]:
    client = VaultClient()
    access = client.rotate_secret(DEFAULT_PATH, "MINIO_ACCESS_KEY", length=16)
    secret = client.rotate_secret(DEFAULT_PATH, "MINIO_SECRET_KEY", length=32)
    return access, secret


def main() -> None:
    rotate_minio()
    logger.info("MinIO credentials rotated in Vault path '%s'", DEFAULT_PATH)


if __name__ == "__main__":
    main()
