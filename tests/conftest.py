import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app
from app.database import get_db, Base
from app.config import Settings

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
def mock_settings(monkeypatch):
    """Mock settings for tests."""
    test_settings = Settings(
        openai_api_key="test-openai-key",
        database_url="sqlite:///./test.db",
        redis_url="redis://localhost:6379",
        celery_broker_url="redis://localhost:6379",
        celery_result_backend="redis://localhost:6379",
        jwt_secret_key="test-secret-key-that-is-long-enough-for-testing-purposes",
        environment="testing"
    )
    monkeypatch.setattr("app.config.settings", test_settings)
    return test_settings


@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
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
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }