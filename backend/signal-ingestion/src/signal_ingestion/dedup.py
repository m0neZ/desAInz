"""Deduplication utilities using Redis Bloom filter."""

from __future__ import annotations

from backend.shared.cache import SyncRedis, get_sync_client
from backend.shared.config import settings as shared_settings
from .settings import settings

redis_client: SyncRedis = get_sync_client()
BLOOM_KEY = "signals:bloom"


def initialize() -> None:
    """Create the bloom filter if it does not already exist."""
    if not redis_client.exists(BLOOM_KEY):
        redis_client.bf().create(
            BLOOM_KEY, settings.dedup_error_rate, settings.dedup_capacity
        )
        redis_client.expire(BLOOM_KEY, settings.dedup_ttl)


def is_duplicate(key: str) -> bool:
    """Return ``True`` if ``key`` already exists in the bloom filter."""
    return bool(redis_client.bf().exists(BLOOM_KEY, key))


def add_key(key: str) -> None:
    """Add ``key`` to the bloom filter and refresh TTL."""
    redis_client.bf().add(BLOOM_KEY, key)
    redis_client.expire(BLOOM_KEY, settings.dedup_ttl)


initialize()
