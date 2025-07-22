"""Deduplication utilities using a Redis set."""

from __future__ import annotations

from backend.shared.cache import SyncRedis, get_sync_client
from backend.shared.config import settings as shared_settings

from .settings import settings

redis_client: SyncRedis = get_sync_client()
SET_KEY = "signals:dedup"


def initialize(ttl: int) -> None:
    """Create the set if it does not already exist and set expiry."""
    if not redis_client.exists(SET_KEY):
        redis_client.sadd(SET_KEY, "__init__")
        redis_client.expire(SET_KEY, ttl)
        redis_client.srem(SET_KEY, "__init__")
    else:
        redis_client.expire(SET_KEY, ttl)


def is_duplicate(key: str) -> bool:
    """Return ``True`` if ``key`` already exists in the set."""
    return bool(redis_client.sismember(SET_KEY, key))


def add_key(key: str) -> None:
    """Add ``key`` to the set and refresh TTL."""
    redis_client.sadd(SET_KEY, key)
    redis_client.expire(SET_KEY, settings.dedup_ttl)


initialize(settings.dedup_ttl)
