"""Application configuration loading."""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, Iterable

from pydantic import field_validator
from dotenv import load_dotenv
from loguru import logger

from app.secrets.vault import VaultClient
from app.read_secret import read_secret

from .auth import AuthSettings
from .vector_store import VectorStoreSettings
from pydantic_settings import BaseSettings

REQUIRED_VARS = ("jwt_secret_key", "database_url", "openai_api_key")


class Settings(BaseSettings):
    """Main application settings."""

    # Environment
    environment: str = "development"
    log_level: str = "INFO"

    # API Keys
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # Database
    database_url: str | None = None

    # Redis/Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Authentication
    jwt_secret_key: str | None = None
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    auth0_domain: str | None = None
    auth0_client_id: str | None = None
    auth0_client_secret: str | None = None
    auth0_audience: str | None = None
    auth0_issuer: str | None = None

    # Vector store
    provider: str = "chromadb"  # chromadb, pinecone, weaviate, qdrant
    path: str = "./data/vector_store"
    pinecone_api_key: str | None = None
    pinecone_environment: str = "us-east1-gcp"
    weaviate_url: str = "http://localhost:8080"
    weaviate_api_key: str | None = None
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None

    enable_tracing: bool = False
    otlp_endpoint: str = "http://localhost:4318"

    # Grouped dataclasses
    auth: AuthSettings | None = None
    vector_store: VectorStoreSettings | None = None

    # CORS
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    class Config:
        extra = "ignore"

    @field_validator("jwt_secret_key")
    @classmethod
    def _validate_jwt_secret(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if len(v) < 32:
            raise ValueError("JWT secret key must be at least 32 characters long")
        if v.lower() in {"your-secret-key", "secret", "changeme"}:
            raise ValueError("JWT secret key cannot be a default or weak value")
        return v


def _validate_required(settings: Settings, required: Iterable[str]) -> None:
    """Ensure required fields are present."""
    missing = [name for name in required if not getattr(settings, name)]
    if not missing:
        return
    msg = f"Missing required configuration: {', '.join(missing)}"
    if settings.environment == "development":
        logger.warning(f"{msg} (ignored in development mode)")
    else:
        logger.error(msg)
        sys.exit(1)


def _load_from_vault() -> Dict[str, Any]:
    vault_addr = os.getenv("VAULT_ADDR")
    vault_token = os.getenv("VAULT_TOKEN")
    vault_path = os.getenv("VAULT_SECRET_PATH", "secret/websets")

    if not (vault_addr and vault_token):
        raise ConnectionError("VAULT_ADDR and VAULT_TOKEN must be set to use Vault.")

    client = VaultClient()
    client.verify_secret_path(vault_path)

    key_map = {
        "openai_api_key": "OPENAI_API_KEY",
        "anthropic_api_key": "ANTHROPIC_API_KEY",
        "database_url": "DATABASE_URL",
        "redis_url": "REDIS_URL",
        "celery_broker_url": "CELERY_BROKER_URL",
        "celery_result_backend": "CELERY_RESULT_BACKEND",
        "jwt_secret_key": "JWT_SECRET_KEY",
        "auth0_client_secret": "AUTH0_CLIENT_SECRET",
        "enable_tracing": "ENABLE_TRACING",
        "otlp_endpoint": "OTLP_ENDPOINT",
    }

    values: Dict[str, Any] = {}
    for field, key in key_map.items():
        value = client.get_secret(vault_path, key)
        if value is not None:
            values[field] = value
    return values


def load_settings() -> Settings:
    """Load configuration from environment and optionally Vault."""
    load_dotenv(".env")

    config_values: Dict[str, Any] = {
        "environment": os.getenv("ENVIRONMENT", "development"),
        "redis_url": os.getenv("REDIS_URL"),
        "celery_broker_url": os.getenv("CELERY_BROKER_URL"),
        "celery_result_backend": os.getenv("CELERY_RESULT_BACKEND"),
        "openai_api_key": read_secret("OPENAI_API_KEY"),
        "anthropic_api_key": read_secret("ANTHROPIC_API_KEY"),
        "database_url": read_secret("DATABASE_URL"),
        "jwt_secret_key": read_secret("JWT_SECRET_KEY"),
        "auth0_client_secret": read_secret("AUTH0_CLIENT_SECRET"),
        "auth0_domain": os.getenv("AUTH0_DOMAIN"),
        "auth0_client_id": os.getenv("AUTH0_CLIENT_ID"),
        "auth0_audience": os.getenv("AUTH0_AUDIENCE"),
        "auth0_issuer": os.getenv("AUTH0_ISSUER"),
        "enable_tracing": os.getenv("ENABLE_TRACING"),
        "otlp_endpoint": os.getenv("OTLP_ENDPOINT"),
    }

    disable_vault = os.getenv("DISABLE_VAULT", os.getenv("DISABLE_VAULT_FOR_LOCAL_DEV", "false")).lower() == "true"
    environment = os.getenv("ENVIRONMENT", "development").lower()

    use_vault = not disable_vault and os.getenv("VAULT_ADDR") and os.getenv("VAULT_TOKEN")

    if environment == "production" and (disable_vault or not use_vault):
        logger.error("Vault is required in production but not properly configured")
        raise SystemExit(1)

    if use_vault:
        try:
            config_values.update(_load_from_vault())
        except Exception as exc:
            logger.error(f"Failed to load settings from Vault: {exc}")
            if os.getenv("ENVIRONMENT", "development").lower() == "production":
                logger.critical("Could not load settings from Vault in production. Exiting.")
                sys.exit(1)
            logger.warning("Falling back to environment variables due to Vault error.")

    filtered = {k: v for k, v in config_values.items() if v is not None}

    # Separate nested models
    auth_keys = AuthSettings.model_fields.keys()
    vector_keys = VectorStoreSettings.model_fields.keys()

    auth_values = {k: filtered.get(k) for k in auth_keys if k in filtered}
    vector_values = {k: filtered.get(k) for k in vector_keys if k in filtered}

    if auth_values:
        filtered["auth"] = auth_values
    if vector_values:
        filtered["vector_store"] = vector_values

    settings = Settings(**filtered)
    _validate_required(settings, REQUIRED_VARS)
    return settings


# Backwards compatibility
validate_settings = load_settings

# Global settings instance used across the application
settings = load_settings()

__all__ = [
    "AuthSettings",
    "VectorStoreSettings",
    "Settings",
    "load_settings",
    "validate_settings",
    "settings",
]
