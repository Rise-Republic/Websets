import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from typing import Callable
import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def disable_rate_limiting(monkeypatch):
    """Disable rate limiting decorators during tests."""
    from app.middleware import rate_limiting

    def _noop(*args, **kwargs) -> Callable:
        def wrapper(func: Callable) -> Callable:
            return func

        return wrapper

    monkeypatch.setattr(rate_limiting.limiter, "limit", _noop)
    monkeypatch.setattr(rate_limiting.user_limiter, "limit", _noop)


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch, mocker):
    """Set environment variables and stub Vault for tests."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://localhost:6379")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "redis://localhost:6379")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-that-is-long-enough-for-testing-purposes")
    monkeypatch.setenv("ENVIRONMENT", "testing")

    monkeypatch.setenv("VAULT_ADDR", "http://test-vault")
    monkeypatch.setenv("VAULT_TOKEN", "test-token")

    mock_vault = mocker.MagicMock()
    mock_vault.secrets.kv.v2.read_secret_version.return_value = {
        'data': {
            'data': {
                'OPENAI_API_KEY': "test-openai-key",
                'DATABASE_URL': "sqlite:///./test.db",
                'JWT_SECRET_KEY': "test-secret-key-that-is-long-enough-for-testing-purposes",
                'REDIS_URL': "redis://localhost:6379",
                'CELERY_BROKER_URL': "redis://localhost:6379",
                'CELERY_RESULT_BACKEND': "redis://localhost:6379",
            }
        }
    }
    mocker.patch('app.secrets.vault.hvac.Client', return_value=mock_vault)
    mocker.patch('hvac.Client', return_value=mock_vault)


@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    from app.database import Base
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """Create a test client with database dependency override."""
    from app.main import app
    from app.database import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_openai(mocker):
    """Mock OpenAI API calls."""
    return mocker.patch('openai.ChatCompletion.create')


@pytest.fixture
def mock_anthropic(mocker):
    """Mock Anthropic API calls."""
    return mocker.patch('anthropic.Anthropic')


@pytest.fixture
def mock_redis(mocker):
    """Mock Redis client."""
    mocker.patch('redis.from_url', return_value=mocker.MagicMock())
    mocker.patch('redis.Redis.from_url', return_value=mocker.MagicMock())
    return mocker.patch('redis.Redis', return_value=mocker.MagicMock())


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }

@pytest.fixture
def mock_settings(mocker):
    """Mock application settings."""
    mock = mocker.patch('app.config.settings', autospec=True)
    mock.jwt_secret_key = "test-secret-key-that-is-long-enough-for-testing-purposes"
    mock.jwt_algorithm = "HS256"
    mock.access_token_expire_minutes = 30
    mock.openai_api_key = "test-openai-key"
    mock.anthropic_api_key = "test-anthropic-key-from-fixture"
    return mock
