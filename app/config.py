from pydantic_settings import BaseSettings
from typing import Optional


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
    
    # Storage
    data_dir: str = "./data"
    vector_store_path: str = "./data/vector_store"
    
    # Crawler Settings
    max_concurrent_crawls: int = 5
    request_delay_ms: int = 1000
    user_agent: str = "WebSetMiner/1.0"
    
    # Environment
    environment: str = "development"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"


settings = Settings()