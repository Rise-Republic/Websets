from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import field_validator
import os
import sys
from loguru import logger

# Import VaultClient to fetch secrets
from app.secrets.vault import VaultClient


def load_secrets_from_vault():
    """
    Load secrets from HashiCorp Vault and set them as environment variables.
    This function is called before settings are loaded.
    """
    vault_addr = os.getenv("VAULT_ADDR")
    vault_token = os.getenv("VAULT_TOKEN")
    vault_secret_path = os.getenv("VAULT_SECRET_PATH", "secret/data/websets")

    if vault_addr and vault_token:
        logger.info(f"Attempting to load secrets from Vault at {vault_addr}")
        try:
            vault_client = VaultClient(url=vault_addr, token=vault_token)
            secrets = vault_client.client.secrets.kv.v2.read_secret_version(path=vault_secret_path)
            if secrets and 'data' in secrets and 'data' in secrets['data']:
                secret_data = secrets['data']['data']
                for key, value in secret_data.items():
                    os.environ[key.upper()] = str(value)
                logger.info(f"Successfully loaded {len(secret_data)} secrets from Vault path '{vault_secret_path}'.")
            else:
                logger.warning("Vault secret path found, but no data was returned.")
        except Exception as e:
            logger.error(f"Failed to load secrets from Vault: {e}")
            # Exit if Vault connection fails to prevent running with missing secrets
            sys.exit(1)
    else:
        logger.info("VAULT_ADDR or VAULT_TOKEN not set. Skipping Vault secret loading.")


class Settings(BaseSettings):
    # API Keys
    openai_api_key: str
    anthropic_api_key: Optional[str] = None
    
    # Database
    database_url: str
    
    # Redis/Celery
    redis_url: str
    celery_broker_url: str
    celery_result_backend: str
    
    # Authentication
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    @field_validator('jwt_secret_key')
    @classmethod
    def validate_jwt_secret(cls, v):
        if not v:
            raise ValueError('JWT secret key is required')
        if len(v) < 32:
            raise ValueError('JWT secret key must be at least 32 characters long for security')
        if v == 'your-secret-key' or v == 'secret' or v == 'changeme':
            raise ValueError('JWT secret key cannot be a default or weak value')
        return v
    
    # Storage
    data_dir: str = "./data"
    vector_store_path: str = "./data/vector_store"
    vector_store_provider: str = "chromadb"  # chromadb, pinecone, weaviate, qdrant
    
    # Vector Store Configurations
    # Pinecone
    pinecone_api_key: Optional[str] = None
    pinecone_environment: str = "us-east1-gcp"
    
    # Weaviate
    weaviate_url: str = "http://localhost:8080"
    weaviate_api_key: Optional[str] = None
    
    # Qdrant
    qdrant_url: Optional[str] = None  # e.g., "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    
    # Object Storage
    object_storage_provider: str = "local"  # local, s3, gcs
    
    # AWS S3 Configuration
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_bucket_name: Optional[str] = None
    
    # Google Cloud Storage Configuration
    gcs_bucket_name: Optional[str] = None
    gcs_credentials_path: Optional[str] = None
    
    # Crawler Settings
    max_concurrent_crawls: int = 5
    request_delay_ms: int = 1000
    user_agent: str = "WebSetMiner/1.0"
    
    # Environment
    environment: str = "development"
    log_level: str = "INFO"
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "https://yourdomain.com"]
    
    model_config = {
        "env_file": ".env" if not os.getenv("VAULT_ADDR") else None,
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


def validate_settings():
    """Validate critical settings at startup."""
    # Load secrets from Vault before initializing settings
    load_secrets_from_vault()

    try:
        settings = Settings()
    
            
        return settings
    except Exception as e:
        logger.error(f"Error validating settings: {e}")
        sys.exit(1)


settings = validate_settings()