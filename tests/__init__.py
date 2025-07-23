import os

# Ensure required environment variables are set before application modules are imported
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-that-is-long-enough-for-testing-purposes")
os.environ.setdefault("ENVIRONMENT", "testing")

# Optional variables used by Celery/Redis
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379")
