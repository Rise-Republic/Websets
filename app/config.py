import os
import sys
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from loguru import logger
from pydantic import field_validator
from pydantic_settings import BaseSettings

# Assuming these are your custom vault client and secret reader
# from app.secrets.vault import VaultClient
# from app.read_secret import read_secret

# --- Mock objects for demonstration since the original files are not available ---
class VaultClient:
    def get_secret(self, path: str, key: str) -> str | None:
        logger.info(f"Mock Vault: Getting '{key}' from '{path}'")
        # In a real scenario, this would interact with Vault.
        # We simulate this by checking environment variables.
        return os.getenv(key)

    def verify_secret_path(self, path: str):
        logger.info(f"Mock Vault: Verifying path '{path}'")
        # In a real scenario, this would check if the path exists.
        return True

def read_secret(key: str) -> str | None:
    """A mock for your custom secret reading function."""
    return os.getenv(key)
# --- End of Mock objects ---


# Define required variables for easy checking
REQUIRED_VARS = ("jwt_secret_key", "database_url", "openai_api_key")

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
    auth: AuthSettings
    vector_store: VectorStoreSettings
    
    # CORS
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    class Config:
        # Pydantic-settings can automatically look for env vars with this prefix.
        # e.g., APP_DATABASE_URL will map to `database_url`.
        # We will load manually here to accommodate the custom `read_secret` and Vault logic.
        extra = "ignore"


# --- Helper Functions (Refactored Logic) ---

def _create_and_validate_settings(config_values: Dict[str, Any]) -> Settings:
    """
    Creates a Settings instance from a dictionary and validates required variables.
    (Recommendation #2: DRY Principle)
    """
    # Separate nested settings from top-level ones
    auth_keys = AuthSettings.model_fields.keys()
    vector_store_keys = VectorStoreSettings.model_fields.keys()

    auth_values = {k: config_values.pop(k) for k in auth_keys if k in config_values}
    vector_store_values = {
        k: config_values.pop(k) for k in vector_store_keys if k in config_values
    }
    
    # Pydantic can now create the nested models automatically
    if auth_values:
        config_values["auth"] = auth_values
    if vector_store_values:
        config_values["vector_store"] = vector_store_values

    # Create the final settings object
    settings = Settings(**config_values)

    # Check for missing required variables
    missing_vars = []
    if not settings.openai_api_key:
        missing_vars.append("openai_api_key")
    if not settings.database_url:
        missing_vars.append("database_url")
    if not settings.auth or not settings.auth.jwt_secret_key:
        missing_vars.append("jwt_secret_key")

    if missing_vars:
        msg = f"Missing required configuration: {', '.join(missing_vars)}"
        if settings.environment == "development":
            logger.warning(f"{msg} (ignored in development mode)")
        else:
            logger.error(msg)
            sys.exit(1)
            
    return settings


def _load_settings_from_vault() -> Settings:
    """Load settings from HashiCorp Vault."""
    logger.info("Attempting to load settings from Vault...")
    vault_addr = os.getenv("VAULT_ADDR")
    vault_token = os.getenv("VAULT_TOKEN")
    vault_path = os.getenv("VAULT_SECRET_PATH", "secret/websets")

    if not (vault_addr and vault_token):
        raise ConnectionError("VAULT_ADDR and VAULT_TOKEN must be set to use Vault.")

    client = VaultClient()
    client.verify_secret_path(vault_path) # Throws an error if path is invalid

    # Define which keys to fetch from Vault
    # Using a mapping to handle potential differences in key names
    VAULT_KEY_MAP = {
        "openai_api_key": "OPENAI_API_KEY",
        "anthropic_api_key": "ANTHROPIC_API_KEY",
        "database_url": "DATABASE_URL",
        "redis_url": "REDIS_URL",
        "celery_broker_url": "CELERY_BROKER_URL",
        "celery_result_backend": "CELERY_RESULT_BACKEND",
        "jwt_secret_key": "JWT_SECRET_KEY",
        "auth0_client_secret": "AUTH0_CLIENT_SECRET",
    }
    
    config_values = {}
    for setting_key, vault_key in VAULT_KEY_MAP.items():
        value = client.get_secret(vault_path, vault_key)
        if value is not None:
            config_values[setting_key] = value

    # Add values that are typically just env vars
    config_values.update({
        "environment": os.getenv("ENVIRONMENT", "development"),
        "auth0_domain": os.getenv("AUTH0_DOMAIN"),
        "auth0_client_id": os.getenv("AUTH0_CLIENT_ID"),
        "auth0_audience": os.getenv("AUTH0_AUDIENCE"),
        "auth0_issuer": os.getenv("AUTH0_ISSUER"),
    })

    logger.info("Successfully loaded configuration from Vault.")
    return _create_and_validate_settings(config_values)


def _load_settings_from_env() -> Settings:
    """
    Load settings from environment variables and .env file.
    (Recommendation #3: Simplified loading)
    """
    logger.info("Loading settings from environment variables and/or .env file.")
    load_dotenv(".env")

    # The custom `read_secret` function is used for sensitive values,
    # falling back to standard `os.getenv` for others.
    config_values = {
        # API Keys & DB
        "openai_api_key": read_secret("OPENAI_API_KEY"),
        "anthropic_api_key": read_secret("ANTHROPIC_API_KEY"),
        "database_url": read_secret("DATABASE_URL"),
        # Auth
        "jwt_secret_key": read_secret("JWT_SECRET_KEY"),
        "auth0_client_secret": read_secret("AUTH0_CLIENT_SECRET"),
        # Other env vars
        "environment": os.getenv("ENVIRONMENT", "development"),
        "redis_url": os.getenv("REDIS_URL"),
        "celery_broker_url": os.getenv("CELERY_BROKER_URL"),
        "celery_result_backend": os.getenv("CELERY_RESULT_BACKEND"),
        "auth0_domain": os.getenv("AUTH0_DOMAIN"),
        "auth0_client_id": os.getenv("AUTH0_CLIENT_ID"),
        "auth0_audience": os.getenv("AUTH0_AUDIENCE"),
        "auth0_issuer": os.getenv("AUTH0_ISSUER"),
    }
    
    # Filter out None values so Pydantic can apply its defaults
    filtered_config = {k: v for k, v in config_values.items() if v is not None}
    
    return _create_and_validate_settings(filtered_config)


def get_settings() -> Settings:
    """
    Main function to get settings.
    It determines whether to use Vault or fallback to environment variables.
    (Recommendation #1: Simplified Control Flow)
    """
    # Check for explicit bypass first
    if os.getenv("DISABLE_VAULT", "false").lower() == "true":
        logger.warning("Vault is explicitly disabled via DISABLE_VAULT. Falling back to environment.")
        return _load_settings_from_env()

    # Check if Vault is configured
    vault_is_configured = "VAULT_ADDR" in os.environ and "VAULT_TOKEN" in os.environ
    environment = os.getenv("ENVIRONMENT", "development").lower()

    if vault_is_configured:
        try:
            return _load_settings_from_vault()
        except Exception as e:
            logger.error(f"Failed to load settings from Vault: {e}")
            if environment != "production":
                logger.warning("Falling back to environment variables due to Vault error.")
                return _load_settings_from_env()
            else:
                logger.critical("Could not load settings from Vault in production. Exiting.")
                sys.exit(1)
    
    # If Vault is not configured
    logger.info("Vault is not configured (VAULT_ADDR or VAULT_TOKEN not set).")
    if environment != "production":
        logger.warning("Proceeding with environment variables for configuration.")
        return _load_settings_from_env()
    else:
        logger.error("Vault is not configured in a production environment. Exiting.")
        sys.exit(1)

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

