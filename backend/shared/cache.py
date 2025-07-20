"""Utility helpers for Redis connections."""

from __future__ import annotations

from typing import Any, Optional, TypeAlias

import redis
from redis import asyncio as aioredis

from .config import settings

SyncRedis: TypeAlias = redis.Redis
AsyncRedis: TypeAlias = aioredis.Redis

__all__ = [
    "SyncRedis",
    "AsyncRedis",
    "get_sync_client",
    "get_async_client",
    "sync_get",
    "sync_set",
    "async_get",
    "async_set",
]


def get_sync_client() -> SyncRedis:
    """Return a synchronous Redis client."""
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def get_async_client() -> AsyncRedis:
    """Return an asynchronous Redis client."""
    return aioredis.Redis.from_url(settings.redis_url, decode_responses=True)


def sync_get(key: str) -> Optional[str]:
    """Return the value for ``key`` using the default synchronous client."""
    return get_sync_client().get(key)


def sync_set(key: str, value: str, ttl: int | None = None) -> None:
    """Set ``key`` to ``value`` optionally expiring after ``ttl`` seconds."""
    client = get_sync_client()
    if ttl is None:
        client.set(key, value)
    else:
        client.setex(key, ttl, value)


async def async_get(key: str) -> Optional[str]:
    """Return the value for ``key`` using the default asynchronous client."""
    client = get_async_client()
    return await client.get(key)


async def async_set(key: str, value: str, ttl: int | None = None) -> None:
    """Set ``key`` to ``value`` optionally expiring after ``ttl`` seconds."""
    client = get_async_client()
    if ttl is None:
        await client.set(key, value)
    else:
        await client.setex(key, ttl, value)
