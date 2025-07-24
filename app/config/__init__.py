"""Application configuration package."""
from __future__ import annotations

import os
from typing import Optional

from loguru import logger
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from .auth import AuthSettings
from .vector_store import VectorStoreSettings
from .env import load_vault_env, load_file_secrets


class Settings(BaseSettings):
    """Main application settings."""

    # Environment
    environment: str = "development"
    log_level: str = "INFO"

    # API Keys
    openai_api_key: str
    anthropic_api_key: Optional[str] = None

    # Database
    database_url: str

    # Redis/Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Nested Settings
    auth: Optional[AuthSettings] = None
    vector_store: Optional[VectorStoreSettings] = None

    # CORS
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # Telemetry
    enable_tracing: bool = False
    otlp_endpoint: str = "http://localhost:4318"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def jwt_secret_key(self) -> Optional[str]:
        if self.auth and self.auth.jwt_secret_key:
            return self.auth.jwt_secret_key
        return os.getenv("JWT_SECRET_KEY")


# ----- Settings loading helpers -----

def get_settings() -> Settings:
    """Return application settings with optional Vault integration."""
    disable_vault = os.getenv("DISABLE_VAULT", "false").lower() == "true"
    env = os.getenv("ENVIRONMENT", "development").lower()
    ci_mode = os.getenv("CI", "false").lower() == "true"

    use_vault = not disable_vault and os.getenv("VAULT_ADDR") and os.getenv("VAULT_TOKEN")
    if use_vault:
        try:
            load_vault_env()
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
    try:
        return Settings()
    except ValidationError as exc:
        logger.error("Invalid configuration: %s", exc)
        raise SystemExit(1) from exc


# Backwards compatibility for older code/tests
validate_settings = get_settings

# Package-level settings instance
settings = get_settings()

__all__ = [
    "AuthSettings",
    "VectorStoreSettings",
    "Settings",
    "get_settings",
    "settings",
]
