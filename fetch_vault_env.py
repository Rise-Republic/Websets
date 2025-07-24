#!/usr/bin/env python3
"""Fetch secrets from Vault and print them in .env format."""

import os
from typing import Dict

from app.secrets.vault import VaultClient

VAULT_PATH = os.getenv("VAULT_SECRET_PATH", "secret/websets")


def fetch_all(path: str) -> Dict[str, str]:
    """Return all secrets stored at the given path."""
    client = VaultClient()
    secret = client.client.secrets.kv.v2.read_secret_version(path=path)
    return secret["data"]["data"]


def main() -> None:
    secrets = fetch_all(VAULT_PATH)
    for key, value in secrets.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
