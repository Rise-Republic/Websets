from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import field_validator
import os
import sys


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
    vector_store_provider: str = "faiss"  # faiss, pinecone, weaviate, qdrant
    
    # Vector Store Configurations
    # Pinecone
    pinecone_api_key: Optional[str] = None
    pinecone_environment: str = "us-east1-gcp"
    
    # Weaviate
    weaviate_url: str = "http://localhost:8080"
    weaviate_api_key: Optional[str] = None
    
    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    
    # Object Storage (AWS S3, GCS)
    object_storage_provider: str = "local"  # local, s3, gcs
    s3_bucket_name: Optional[str] = None
    s3_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    gcs_bucket_name: Optional[str] = None
    gcs_credentials_path: Optional[str] = None
    
    # Crawler Settings
    max_concurrent_crawls: int = 5
    request_delay_ms: int = 1000
    user_agent: str = "WebSetMiner/1.0"
    
    # Environment
    environment: str = "development"
    log_level: str = "INFO"
    allowed_origins: list[str] = ["http://localhost:3000", "https://yourdomain.com"]
    
    class Config:
        env_file = ".env"


def validate_settings():
    """Validate critical settings at startup."""
    try:
        settings = Settings()
        
        # Check for required environment variables
        required_vars = ['JWT_SECRET_KEY', 'DATABASE_URL', 'OPENAI_API_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
            sys.exit(1)
            
        return settings
    except Exception as e:
        print(f"Error validating settings: {e}")
        sys.exit(1)


settings = validate_settings()