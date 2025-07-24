#!/usr/bin/env python3
"""Rotate MinIO credentials in Vault and output new values."""

import os
from app.secrets.vault import VaultClient


def main() -> None:
    vault_path = os.getenv("MINIO_VAULT_PATH", "secret/websets")
    client = VaultClient()
    access_key = client.rotate_secret(vault_path, "MINIO_ACCESS_KEY", length=16)
    secret_key = client.rotate_secret(vault_path, "MINIO_SECRET_KEY", length=32)
    print(f"MINIO_ACCESS_KEY={access_key}")
    print(f"MINIO_SECRET_KEY={secret_key}")


if __name__ == "__main__":
    main()
