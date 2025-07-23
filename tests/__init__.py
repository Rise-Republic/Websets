import os

# Ensure required environment variables are set before application modules are imported
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-that-is-long-enough-for-testing-purposes")
os.environ.setdefault("ENVIRONMENT", "testing")

os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379")

os.environ.setdefault("VAULT_ADDR", "http://test-vault")
os.environ.setdefault("VAULT_TOKEN", "test-token")

from unittest.mock import MagicMock
import hvac

_mock_vault = MagicMock()
_mock_vault.secrets.kv.v2.read_secret_version.return_value = {
    'data': {
        'data': {
            'OPENAI_API_KEY': os.environ["OPENAI_API_KEY"],
            'DATABASE_URL': os.environ["DATABASE_URL"],
            'JWT_SECRET_KEY': os.environ["JWT_SECRET_KEY"],
            'REDIS_URL': os.environ["REDIS_URL"],
            'CELERY_BROKER_URL': os.environ["CELERY_BROKER_URL"],
            'CELERY_RESULT_BACKEND': os.environ["CELERY_RESULT_BACKEND"],
        }
    }
}
hvac.Client = MagicMock(return_value=_mock_vault)
