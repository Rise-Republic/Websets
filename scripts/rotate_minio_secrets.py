#!/usr/bin/env python3
"""Rotate MinIO credentials stored in Vault."""
import os
import sys
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
    access, secret = rotate_minio()
    print(f"export MINIO_ACCESS_KEY={access}")
    print(f"export MINIO_SECRET_KEY={secret}")
    print(f"MinIO credentials rotated in Vault path '{DEFAULT_PATH}'")


if __name__ == "__main__":
    main()
