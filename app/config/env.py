"""Helpers for loading configuration from the environment and Vault."""
from __future__ import annotations

import os
from typing import Dict

from dotenv import load_dotenv
from loguru import logger

from app.secrets.vault import VaultClient
from app.read_secret import read_secret


# Mapping of Settings fields to environment variable or Vault keys
SECRET_KEY_MAP: Dict[str, str] = {
    "openai_api_key": "OPENAI_API_KEY",
    "anthropic_api_key": "ANTHROPIC_API_KEY",
    "database_url": "DATABASE_URL",
    "redis_url": "REDIS_URL",
    "celery_broker_url": "CELERY_BROKER_URL",
    "celery_result_backend": "CELERY_RESULT_BACKEND",
    "jwt_secret_key": "JWT_SECRET_KEY",
    "auth0_client_secret": "AUTH0_CLIENT_SECRET",
}


def load_vault_values() -> Dict[str, str]:
    """Fetch secrets from HashiCorp Vault using :data:`SECRET_KEY_MAP`."""
    vault_addr = os.getenv("VAULT_ADDR")
    vault_token = os.getenv("VAULT_TOKEN")
    if not (vault_addr and vault_token):
        raise ConnectionError("VAULT_ADDR and VAULT_TOKEN must be set to use Vault")

    path = os.getenv("VAULT_SECRET_PATH", "secret/websets")
    client = VaultClient()
    client.verify_secret_path(path)

    values: Dict[str, str] = {}
    for field, key in SECRET_KEY_MAP.items():
        value = client.get_secret(path, key)
        if value is not None:
            os.environ[key] = value
            values[field] = value
    return values


def load_file_secrets() -> None:
    """Populate ``os.environ`` from files under /run/secrets if present."""
    for key in SECRET_KEY_MAP.values():
        value = read_secret(key)
        if value is not None:
            os.environ.setdefault(key, value)


def load_environment() -> Dict[str, str]:
    """Load environment variables and optional Vault secrets."""
    load_dotenv(".env")

    disable_vault = os.getenv("DISABLE_VAULT", "false").lower() == "true"
    env = os.getenv("ENVIRONMENT", "development").lower()
    ci_mode = os.getenv("CI", "false").lower() == "true"

    use_vault = not disable_vault and os.getenv("VAULT_ADDR") and os.getenv("VAULT_TOKEN")

    values: Dict[str, str] = {}
    if use_vault:
        try:
            values.update(load_vault_values())
        except Exception as exc:  # pragma: no cover - network failure
            if env != "production":
                logger.warning("Vault error %s, falling back to environment", exc)
            else:
                logger.critical("Failed to load settings from Vault: %s", exc)
                raise SystemExit(1) from exc
    else:
        if env == "production" and not ci_mode:
            logger.critical("Vault is required in production")
            raise SystemExit(1)
        load_file_secrets()

    return values
