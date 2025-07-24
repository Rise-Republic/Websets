import asyncio
import json
import os
import pytest

os.environ.setdefault("OPENAI_API_KEY", "x")
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("REDIS_URL", "redis://")
os.environ.setdefault("CELERY_BROKER_URL", "redis://")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://")
os.environ.setdefault("JWT_SECRET_KEY", "x" * 32)

from app.utils import cache
from unittest.mock import MagicMock

class DummyMetrics:
    def __init__(self):
        self.calls = []
    def record_cache_operation(self, op, result):
        self.calls.append((op, result))

@pytest.fixture(autouse=True)
def patch_to_thread(monkeypatch):
    async def immediate(func, *args, **kwargs):
        return func(*args, **kwargs)
    monkeypatch.setattr(asyncio, "to_thread", immediate)

@pytest.fixture
def metrics(monkeypatch):
    m = DummyMetrics()
    monkeypatch.setattr(cache, "metrics", lambda: m)
    return m

@pytest.fixture
def redis(monkeypatch):
    client = MagicMock()
    monkeypatch.setattr(cache, "redis_client", client)
    return client

@pytest.mark.asyncio
async def test_get_cached_hit(redis, metrics):
    redis.get.return_value = json.dumps({"data": 1})
    result = await cache.get_cached_dataset_records("d", 1, 10)
    assert result == {"data": 1}
    assert ("get", "hit") in metrics.calls

@pytest.mark.asyncio
async def test_get_cached_miss(redis, metrics):
    redis.get.return_value = None
    result = await cache.get_cached_dataset_records("d", 1, 10)
    assert result is None
    assert ("get", "miss") in metrics.calls

@pytest.mark.asyncio
async def test_set_cached_success(redis, metrics):
    await cache.set_cached_dataset_records("d", 1, 10, {"a": 2})
    redis.setex.assert_called_once()
    assert ("set", "success") in metrics.calls

@pytest.mark.asyncio
async def test_invalidate_error(redis, metrics, monkeypatch):
    redis.keys.side_effect = Exception("fail")
    await cache.invalidate_dataset_records("d")
    assert ("invalidate", "error") in metrics.calls
