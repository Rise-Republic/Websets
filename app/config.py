import os
import sys
from typing import Optional

from dotenv import load_dotenv
from loguru import logger
from pydantic import ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.secrets.vault import VaultClient
from app.read_secret import read_secret


# Define required variables for easy checking
# Mapping of Settings fields to environment variable or Vault keys
SECRET_KEY_MAP = {
    "openai_api_key": "OPENAI_API_KEY",
    "anthropic_api_key": "ANTHROPIC_API_KEY",
    "database_url": "DATABASE_URL",
    "redis_url": "REDIS_URL",
    "celery_broker_url": "CELERY_BROKER_URL",
    "celery_result_backend": "CELERY_RESULT_BACKEND",
    "jwt_secret_key": "JWT_SECRET_KEY",
    "auth0_client_secret": "AUTH0_CLIENT_SECRET",
}

# --- Structured Settings using Nested Models (Recommendation #4) ---

class AuthSettings(BaseSettings):
    """Authentication related settings."""
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    auth0_domain: Optional[str] = None
    auth0_client_id: Optional[str] = None
    auth0_client_secret: Optional[str] = None
    auth0_audience: Optional[str] = None
    auth0_issuer: Optional[str] = None

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

class VectorStoreSettings(BaseSettings):
    """Settings for vector storage providers."""
    provider: str = "chromadb"  # chromadb, pinecone, weaviate, qdrant
    path: str = "./data/vector_store"
    # Pinecone
    pinecone_api_key: Optional[str] = None
    pinecone_environment: str = "us-east1-gcp"
    # Weaviate
    weaviate_url: str = "http://localhost:8080"
    weaviate_api_key: Optional[str] = None
    # Qdrant
    qdrant_url: Optional[str] = None  # e.g., "http://localhost:6333"
    qdrant_api_key: Optional[str] = None


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


# --- Settings loading helpers ---


def _load_vault_values() -> dict[str, str]:
    """Fetch secrets from HashiCorp Vault using ``SECRET_KEY_MAP``."""
    vault_addr = os.getenv("VAULT_ADDR")
    vault_token = os.getenv("VAULT_TOKEN")
    if not (vault_addr and vault_token):
        raise ConnectionError("VAULT_ADDR and VAULT_TOKEN must be set to use Vault")

    path = os.getenv("VAULT_SECRET_PATH", "secret/websets")
    client = VaultClient()
    client.verify_secret_path(path)

    values: dict[str, str] = {}
    for field, key in SECRET_KEY_MAP.items():
        value = client.get_secret(path, key)
        if value is not None:
            os.environ[key] = value
            values[field] = value
    return values


def _load_file_secrets() -> None:
    """Populate ``os.environ`` from files under /run/secrets if present."""
    for key in SECRET_KEY_MAP.values():
        value = read_secret(key)
        if value is not None:
            os.environ.setdefault(key, value)


def get_settings() -> Settings:
    """Return application settings with optional Vault integration."""
    load_dotenv(".env")

    disable_vault = os.getenv("DISABLE_VAULT", "false").lower() == "true"
    env = os.getenv("ENVIRONMENT", "development").lower()
    ci_mode = os.getenv("CI", "false").lower() == "true"

    use_vault = not disable_vault and os.getenv("VAULT_ADDR") and os.getenv("VAULT_TOKEN")

    values: dict[str, str] = {}
    if use_vault:
        try:
            values.update(_load_vault_values())
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
        _load_file_secrets()

    try:
        return Settings(**values)
    except ValidationError as exc:
        logger.error("Invalid configuration: %s", exc)
        raise SystemExit(1) from exc


# Backwards compatibility for older code/tests
validate_settings = get_settings

# --- Main entry point ---
settings = get_settings()

# Example of how to use the settings object
if __name__ == "__main__":
    logger.info(f"Settings loaded for '{settings.environment}' environment.")
    logger.info(f"Database URL: {settings.database_url}")
    logger.info(f"Allowed origins: {settings.allowed_origins}")
    if settings.auth:
        logger.info(f"JWT Algorithm: {settings.auth.jwt_algorithm}")
    if settings.vector_store:
        logger.info(f"Vector Store Provider: {settings.vector_store.provider}")

