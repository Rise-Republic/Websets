#!/usr/bin/env python3
"""Fetch secrets from Vault and log the keys fetched."""

import os
from typing import Dict
from loguru import logger

from app.secrets.vault import VaultClient

VAULT_PATH = os.getenv("VAULT_SECRET_PATH", "secret/websets")


def fetch_all(path: str) -> Dict[str, str]:
    """Return all secrets stored at the given path."""
    client = VaultClient()
    return client.fetch_all(path)


def main() -> None:
    secrets = fetch_all(VAULT_PATH)
    for key in secrets:
        logger.info(f"Fetched secret for {key}")


if __name__ == "__main__":
    main()
