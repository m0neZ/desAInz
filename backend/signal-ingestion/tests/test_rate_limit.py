"""Tests for adapter rate limiting."""

from __future__ import annotations

import asyncio
from time import perf_counter
import warnings
import os
import sys

import fakeredis.aioredis
import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from signal_ingestion.rate_limit import AdapterRateLimiter  # noqa: E402

warnings.filterwarnings("ignore", category=ResourceWarning)


@pytest.mark.asyncio()  # type: ignore[misc]
async def test_limiter_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure acquiring more than the limit waits for tokens."""
    async with fakeredis.aioredis.FakeRedis() as redis:
        limiter = AdapterRateLimiter({"foo": 1}, redis=redis)
        start = perf_counter()
        await limiter.acquire("foo")
        await limiter.acquire("foo")
        await redis.connection_pool.disconnect()
        elapsed = perf_counter() - start
        assert elapsed >= 1


@pytest.mark.asyncio()  # type: ignore[misc]
async def test_limiter_allows_unlimited() -> None:
    """Adapters without a limit never block."""
    async with fakeredis.aioredis.FakeRedis() as redis:
        limiter = AdapterRateLimiter({}, redis=redis)
        start = perf_counter()
        await limiter.acquire("bar")
        await redis.connection_pool.disconnect()
        elapsed = perf_counter() - start
        assert elapsed < 1
