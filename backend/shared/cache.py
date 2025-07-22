"""Utility helpers for Redis connections."""

from __future__ import annotations

from typing import Optional, TypeAlias, cast

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
    "sync_delete",
    "async_get",
    "async_set",
    "async_delete",
]


_SYNC_CLIENT: SyncRedis = redis.Redis.from_url(
    str(settings.redis_url), decode_responses=True
)


def get_sync_client() -> SyncRedis:
    """Return the cached synchronous Redis client."""
    return _SYNC_CLIENT


_ASYNC_CLIENT: AsyncRedis = aioredis.Redis.from_url(
    str(settings.redis_url), decode_responses=True
)


def get_async_client() -> AsyncRedis:
    """Return the cached asynchronous Redis client."""
    return _ASYNC_CLIENT


def sync_get(key: str, client: SyncRedis | None = None) -> Optional[str]:
    """Return the value for ``key`` using the provided or default sync client."""
    cli = client or get_sync_client()
    return cast(Optional[str], cli.get(key))


def sync_set(
    key: str, value: str, ttl: int | None = None, client: SyncRedis | None = None
) -> None:
    """Set ``key`` to ``value`` optionally expiring after ``ttl`` seconds."""
    cli = client or get_sync_client()
    if ttl is None:
        cli.set(key, value)
    else:
        cli.setex(key, ttl, value)


def sync_delete(key: str, client: SyncRedis | None = None) -> None:
    """Delete ``key`` using the provided or default sync client."""
    cli = client or get_sync_client()
    cli.delete(key)


async def async_get(key: str, client: AsyncRedis | None = None) -> Optional[str]:
    """Return the value for ``key`` using the provided or default async client."""
    cli = client or get_async_client()
    return cast(Optional[str], await cli.get(key))


async def async_set(
    key: str,
    value: str,
    ttl: int | None = None,
    client: AsyncRedis | None = None,
) -> None:
    """Set ``key`` to ``value`` optionally expiring after ``ttl`` seconds."""
    cli = client or get_async_client()
    if ttl is None:
        await cli.set(key, value)
    else:
        await cli.setex(key, ttl, value)


async def async_delete(key: str, client: AsyncRedis | None = None) -> None:
    """Delete ``key`` using the provided or default async client."""
    cli = client or get_async_client()
    await cli.delete(key)
