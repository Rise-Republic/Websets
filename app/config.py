
from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import field_validator
import os
import sys
from app.secrets.vault import VaultClient


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
        "env_file": ".env",
        "extra": "ignore"
    }


# --- Vault integration for secrets ---
def get_secret_from_vault_or_env(key, default=None):
    vault_path = os.getenv("VAULT_SECRET_PATH", "secret/websets")
    try:
        vault = VaultClient()
        value = vault.get_secret(vault_path, key)
        if value:
            return value
    except Exception:
        pass
    return os.getenv(key, default)


def validate_settings():
    """Validate critical settings at startup, using Vault if available."""
    try:
        # Print all VAULT_ env vars for debug
        print("[config.py] VAULT_ env vars:")
        for k, v in os.environ.items():
            if k.startswith("VAULT_"):
                print(f"  {k}={v}")
        # Gather all required secrets
        secret_values = {
            'openai_api_key': get_secret_from_vault_or_env('OPENAI_API_KEY'),
            'anthropic_api_key': get_secret_from_vault_or_env('ANTHROPIC_API_KEY'),
            'database_url': get_secret_from_vault_or_env('DATABASE_URL'),
            'redis_url': get_secret_from_vault_or_env('REDIS_URL'),
            'celery_broker_url': get_secret_from_vault_or_env('CELERY_BROKER_URL'),
            'celery_result_backend': get_secret_from_vault_or_env('CELERY_RESULT_BACKEND'),
            'jwt_secret_key': get_secret_from_vault_or_env('JWT_SECRET_KEY'),
        }
        print("[config.py] Required secrets loaded:")
        for k, v in secret_values.items():
            print(f"  {k}={'***' if v else None}")
            if v is None:
                print(f"[config.py] WARNING: Secret '{k}' is missing (None)")
        # Only pass expected fields to Settings
        settings = Settings(**secret_values)
        # Check for required variables
        required_vars = ['jwt_secret_key', 'database_url', 'openai_api_key']
        missing_vars = [var for var in required_vars if not getattr(settings, var)]
        if missing_vars:
            print(f"Error: Missing required secrets: {', '.join(missing_vars)}")
            sys.exit(1)
        return settings
    except Exception as e:
        print(f"Error validating settings: {e}")
        sys.exit(1)

settings = validate_settings()