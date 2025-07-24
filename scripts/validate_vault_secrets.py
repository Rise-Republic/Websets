#!/usr/bin/env python3
"""Validate that required secrets exist in Vault and are non-empty."""

import json
import os
import sys
from pathlib import Path

# Ensure we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.secrets.vault import VaultClient

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "vault_secrets_template.json"
VAULT_PATH = os.getenv("VAULT_SECRET_PATH", "secret/websets")


def main() -> None:
    try:
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            required = json.load(f)
    except Exception as exc:
        print(f"Error reading template {TEMPLATE_PATH}: {exc}")
        sys.exit(1)

    client = VaultClient()
    missing: list[str] = []
    for key in required.keys():
        value = client.get_secret(VAULT_PATH, key)
        if not value:
            missing.append(key)

    if missing:
        print(f"Missing or empty secrets in '{VAULT_PATH}': {', '.join(missing)}")
        sys.exit(1)

    print(f"All required secrets present in '{VAULT_PATH}'.")


if __name__ == "__main__":
    main()
