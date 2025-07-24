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
# Default path used when the template only lists keys
DEFAULT_PATH = os.getenv("VAULT_SECRET_PATH", "secret/websets")


def main() -> None:
    try:
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            template = json.load(f)
    except Exception as exc:
        print(f"Error reading template {TEMPLATE_PATH}: {exc}")
        sys.exit(1)

    # Determine if the template lists a single path or multiple paths
    if all(not isinstance(v, dict) for v in template.values()):
        paths = {DEFAULT_PATH: list(template.keys())}
    else:
        paths = {
            p: list(keys.keys())
            for p, keys in template.items()
            if isinstance(keys, dict)
        }

    client = VaultClient()
    missing: dict[str, list[str]] = {}
    for path, keys in paths.items():
        for key in keys:
            value = client.get_secret(path, key)
            if not value:
                missing.setdefault(path, []).append(key)

    if missing:
        for path, keys in missing.items():
            print(f"Missing or empty secrets in '{path}': {', '.join(keys)}")
        sys.exit(1)

    print("All required secrets are present in Vault.")


if __name__ == "__main__":
    main()