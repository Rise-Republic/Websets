import asyncio
import json
from typing import Optional

import redis

from app.config import settings
from app.monitoring import get_metrics_collector

# Redis client for caching
redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)


def metrics():
    return get_metrics_collector()


CACHE_TTL_SECONDS = 300


def _key(dataset_id: str, page: int, size: int, tenant_id: str) -> str:
    return f"dataset_records:{tenant_id}:{dataset_id}:{page}:{size}"


async def get_cached_dataset_records(
    dataset_id: str, page: int, size: int, tenant_id: str
) -> Optional[dict]:
    """Retrieve cached dataset records if present."""
    key = _key(dataset_id, page, size, tenant_id)
    try:
        data = await asyncio.to_thread(redis_client.get, key)
        if data:
            metrics().record_cache_operation("get", "hit")
            return json.loads(data)
        metrics().record_cache_operation("get", "miss")
    except Exception:
        metrics().record_cache_operation("get", "error")
    return None


async def set_cached_dataset_records(
    dataset_id: str, page: int, size: int, tenant_id: str, value: dict
) -> None:
    """Cache dataset records for a short time."""
    key = _key(dataset_id, page, size, tenant_id)
    try:
        await asyncio.to_thread(
            redis_client.setex, key, CACHE_TTL_SECONDS, json.dumps(value)
        )
        metrics().record_cache_operation("set", "success")
    except Exception:
        metrics().record_cache_operation("set", "error")


async def invalidate_dataset_records(dataset_id: str) -> None:
    """Remove cached records for a dataset."""
    pattern = f"dataset_records:*:{dataset_id}:*"
    try:
        keys = await asyncio.to_thread(redis_client.keys, pattern)
        if keys:
            await asyncio.to_thread(redis_client.delete, *keys)
        metrics().record_cache_operation("invalidate", "success")
    except Exception:
        metrics().record_cache_operation("invalidate", "error")
