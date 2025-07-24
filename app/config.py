import os
import sys
from typing import Optional

from loguru import logger
from pydantic import ValidationError, field_validator, Field
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
    jwt_secret_key: str = Field(validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(30, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    auth0_domain: Optional[str] = Field(None, validation_alias="AUTH0_DOMAIN")
    auth0_client_id: Optional[str] = Field(None, validation_alias="AUTH0_CLIENT_ID")
    auth0_client_secret: Optional[str] = Field(None, validation_alias="AUTH0_CLIENT_SECRET")
    auth0_audience: Optional[str] = Field(None, validation_alias="AUTH0_AUDIENCE")
    auth0_issuer: Optional[str] = Field(None, validation_alias="AUTH0_ISSUER")

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
    provider: str = Field("chromadb", validation_alias="VECTOR_STORE_PROVIDER")
    path: str = Field("./data/vector_store", validation_alias="VECTOR_STORE_PATH")
    # Pinecone
    pinecone_api_key: Optional[str] = Field(None, validation_alias="PINECONE_API_KEY")
    pinecone_environment: str = Field("us-east1-gcp", validation_alias="PINECONE_ENVIRONMENT")
    # Weaviate
    weaviate_url: str = Field("http://localhost:8080", validation_alias="WEAVIATE_URL")
    weaviate_api_key: Optional[str] = Field(None, validation_alias="WEAVIATE_API_KEY")
    # Qdrant
    qdrant_url: Optional[str] = Field(None, validation_alias="QDRANT_URL")  # e.g., "http://localhost:6333"
    qdrant_api_key: Optional[str] = Field(None, validation_alias="QDRANT_API_KEY")


class Settings(BaseSettings):
    """Main application settings."""
    # Environment
    environment: str = "development"
    log_level: str = "DEBUG"
    
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
    """Populate ``os.environ`` from files under /run/secrets if present."""
    for key in SECRET_KEY_MAP.values():
        value = read_secret(key)
        if value is not None:
            os.environ.setdefault(key, value)


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
                logger.warning(f"Vault error: {exc}, falling back to environment")
            else:
                logger.critical(f"Failed to load settings from Vault: {exc}")
                raise SystemExit(1) from exc
    else:
        if env == "production" and not ci_mode:
            logger.critical("Vault is required in production")
            raise SystemExit(1)
        _load_file_secrets()
    try:
        return Settings()
    except ValidationError as exc:
        # Fix error logging format to properly display validation errors
        logger.error(f"Invalid configuration: {exc}")
        # Print detailed error for debugging
        print(f"\nDETAILED CONFIG ERROR: {exc}\n")
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

