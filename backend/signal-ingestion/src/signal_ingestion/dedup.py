"""Deduplication utilities using Redis Bloom filter."""

from __future__ import annotations

import redis

redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
BLOOM_KEY = "signals:bloom"


def is_duplicate(key: str) -> bool:
    """Return True if ``key`` already exists in the bloom filter."""
    return bool(redis_client.bfExists(BLOOM_KEY, key))


def add_key(key: str) -> None:
    """Add ``key`` to the bloom filter."""
    redis_client.bfAdd(BLOOM_KEY, key)
