
from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import field_validator
import os
import sys
from dotenv import load_dotenv
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
    auth0_domain: Optional[str] = None
    auth0_client_id: Optional[str] = None
    auth0_client_secret: Optional[str] = None
    auth0_audience: Optional[str] = None
    auth0_issuer: Optional[str] = None
    
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
    enable_tracing: bool = False
    otlp_endpoint: str = "http://localhost:4318"
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "https://yourdomain.com",
    ]
    
    model_config = {
        "extra": "ignore"
    }


# --- Vault integration for secrets ---
def get_secret_from_vault(client: VaultClient, path: str, key: str) -> str | None:
    """Fetch a secret key from Vault and raise on failure."""
    try:
        value = client.get_secret(path, key)
        if value is None:
            raise KeyError(f"Secret '{key}' not found at {path}")
        return value
    except Exception as e:
        print(f"[config.py] Vault error retrieving '{key}': {e}")
        raise


def validate_settings():
    """Validate critical settings at startup and require Vault."""
    try:
        # Check if Vault integration should be disabled for local development
        disable_vault = os.getenv("DISABLE_VAULT_FOR_LOCAL_DEV", "false").lower() == "true"

        if disable_vault:
            print("[config.py] Vault integration bypassed for local development.")
            # Load values from .env so local developers can store non-secret keys there
            load_dotenv(".env")

            # Load secrets directly from environment variables
            secret_values = {
                'openai_api_key': os.getenv('OPENAI_API_KEY'),
                'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
                'database_url': os.getenv('DATABASE_URL'),
                'redis_url': os.getenv('REDIS_URL'),
                'celery_broker_url': os.getenv('CELERY_BROKER_URL'),
                'celery_result_backend': os.getenv('CELERY_RESULT_BACKEND'),
                'jwt_secret_key': os.getenv('JWT_SECRET_KEY'),
                'auth0_domain': os.getenv('AUTH0_DOMAIN'),
                'auth0_client_id': os.getenv('AUTH0_CLIENT_ID'),
                'auth0_client_secret': os.getenv('AUTH0_CLIENT_SECRET'),
                'auth0_audience': os.getenv('AUTH0_AUDIENCE'),
                'auth0_issuer': os.getenv('AUTH0_ISSUER'),
            }
            # Only pass expected fields to Settings
            settings = Settings(**secret_values)
            # Check for required variables
            required_vars = ['jwt_secret_key', 'database_url', 'openai_api_key']
            missing_vars = [var for var in required_vars if not getattr(settings, var)]
            if missing_vars:
                print(f"Error: Missing required secrets: {', '.join(missing_vars)}")
                sys.exit(1)
            return settings
        else:
            # Original Vault logic
            load_dotenv(".env")
            vault_addr = os.getenv("VAULT_ADDR")
            vault_token = os.getenv("VAULT_TOKEN")
            vault_path = os.getenv("VAULT_SECRET_PATH", "secret/websets")
            if not vault_addr or not vault_token:
                print("Error: VAULT_ADDR and VAULT_TOKEN must be set for secrets")
                sys.exit(1)

            print("[config.py] VAULT_ env vars:")
            for k, v in os.environ.items():
                if k.startswith("VAULT_"):
                    print(f"  {k}={v}")

            client = VaultClient()
            client.verify_secret_path(vault_path)

            secret_values = {
                'openai_api_key': get_secret_from_vault(client, vault_path, 'OPENAI_API_KEY'),
                'anthropic_api_key': client.get_secret(vault_path, 'ANTHROPIC_API_KEY'),
                'database_url': get_secret_from_vault(client, vault_path, 'DATABASE_URL'),
                'redis_url': client.get_secret(vault_path, 'REDIS_URL'),
                'celery_broker_url': client.get_secret(vault_path, 'CELERY_BROKER_URL'),
                'celery_result_backend': client.get_secret(vault_path, 'CELERY_RESULT_BACKEND'),
                'jwt_secret_key': get_secret_from_vault(client, vault_path, 'JWT_SECRET_KEY'),
                'auth0_domain': client.get_secret(vault_path, 'AUTH0_DOMAIN'),
                'auth0_client_id': client.get_secret(vault_path, 'AUTH0_CLIENT_ID'),
                'auth0_client_secret': client.get_secret(vault_path, 'AUTH0_CLIENT_SECRET'),
                'auth0_audience': client.get_secret(vault_path, 'AUTH0_AUDIENCE'),
                'auth0_issuer': client.get_secret(vault_path, 'AUTH0_ISSUER'),
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
