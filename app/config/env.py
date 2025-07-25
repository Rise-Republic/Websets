from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from app.secrets.vault import VaultClient

# Directory for Docker secrets
SECRETS_DIR = Path('/run/secrets')

# Mapping of Settings fields to environment variable or Vault keys
SECRET_KEY_MAP = {
    "openai_api_key": "OPENAI_API_KEY",
    "anthropic_api_key": "ANTHROPIC_API_KEY",
    "database_url": "DATABASE_URL",
    "redis_url": "REDIS_URL",
    "celery_broker_url": "CELERY_BROKER_URL",
    "celery_result_backend": "CELERY_RESULT_BACKEND",
    "jwt_secret_key": "JWT_SECRET_KEY",
}


def read_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    """Read a secret from ``/run/secrets/<name>`` if present, else from env."""
    path = SECRETS_DIR / name
    if path.exists():
        try:
            return path.read_text().strip()
        except Exception:  # pragma: no cover - file access failures
            pass
    return os.getenv(name, default)


def load_vault_env() -> None:
    """Populate ``os.environ`` with secrets from HashiCorp Vault."""
    vault_addr = os.getenv("VAULT_ADDR")
    vault_token = os.getenv("VAULT_TOKEN")
    if not (vault_addr and vault_token):
        raise ConnectionError("VAULT_ADDR and VAULT_TOKEN must be set to use Vault")

    path = os.getenv("VAULT_SECRET_PATH", "websets")
    client = VaultClient()
    client.verify_secret_path(path)

    for key in SECRET_KEY_MAP.values():
        value = client.get_secret(path, key)
        if value is not None:
            os.environ[key] = value


def _load_file_secrets() -> None:
    """Populate ``os.environ`` from files under ``/run/secrets`` if present."""
    for key in SECRET_KEY_MAP.values():
        value = read_secret(key)
        if value is not None:
            os.environ.setdefault(key, value)
