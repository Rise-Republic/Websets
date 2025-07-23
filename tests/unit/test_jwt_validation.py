import pytest
from hypothesis import given, strategies as st
from pydantic import ValidationError

from app.config import Settings

@pytest.mark.unit
@given(secret=st.text(min_size=1, max_size=31))
def test_jwt_secret_too_short(secret):
    with pytest.raises(ValidationError):
        Settings(jwt_secret_key=secret,
                 openai_api_key="k",
                 database_url="sqlite://",
                 redis_url="redis://",
                 celery_broker_url="redis://",
                 celery_result_backend="redis://")

@pytest.mark.unit
@given(secret=st.text(min_size=32))
def test_jwt_secret_valid(secret):
    s = Settings(jwt_secret_key=secret,
                 openai_api_key="k",
                 database_url="sqlite://",
                 redis_url="redis://",
                 celery_broker_url="redis://",
                 celery_result_backend="redis://")
    assert s.jwt_secret_key == secret
