"""Utility helpers for Redis connections."""

from __future__ import annotations

import redis
from redis import asyncio as aioredis

from .config import settings

__all__ = ["get_sync_client", "get_async_client"]


def get_sync_client() -> redis.Redis:
    """Return a synchronous Redis client."""
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def get_async_client() -> aioredis.Redis:
    """Return an asynchronous Redis client."""
    return aioredis.Redis.from_url(settings.redis_url, decode_responses=True)
