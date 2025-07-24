"""Application configuration package."""
from __future__ import annotations

import os
from typing import Optional

from loguru import logger
from pydantic import ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .auth import AuthSettings
from .vector_store import VectorStoreSettings
from .env import load_environment


class Settings(BaseSettings):
    """Main application settings."""

    # Environment
    environment: str = "development"
    log_level: str = "INFO"

    # API Keys
    openai_api_key: str
    anthropic_api_key: Optional[str] = None

    # Authentication
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if not v:
            raise ValueError("JWT secret key is required")
        if len(v) < 32:
            raise ValueError("JWT secret key must be at least 32 characters long")
        if v.lower() in ("your-secret-key", "secret", "changeme"):
            raise ValueError("JWT secret key cannot be a default or weak value")
        return v

    # Database
    database_url: str

    # Redis/Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Observability
    enable_tracing: bool = False
    otlp_endpoint: str = "http://localhost:4318/v1/traces"

    # Nested Settings
    auth: Optional[AuthSettings] = None
    vector_store: Optional[VectorStoreSettings] = None

    # CORS
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

def get_settings() -> Settings:
    """Return application settings with optional Vault integration."""
    values = load_environment()
    try:
        return Settings(**values)
    except ValidationError as exc:
        logger.error("Invalid configuration: %s", exc)
        raise SystemExit(1) from exc


# Backwards compatibility for older code/tests
validate_settings = get_settings

# --- Main entry point ---
settings = get_settings()


__all__ = ["Settings", "get_settings", "validate_settings", "settings", "AuthSettings", "VectorStoreSettings"]

