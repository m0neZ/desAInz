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
    redis = fakeredis.aioredis.FakeRedis()
    limiter = AdapterRateLimiter({"foo": 1}, redis=redis)
    start = perf_counter()
    await limiter.acquire("foo")
    await limiter.acquire("foo")
    elapsed = perf_counter() - start
    assert elapsed >= 1


@pytest.mark.asyncio()  # type: ignore[misc]
async def test_limiter_allows_unlimited() -> None:
    """Adapters without a limit never block."""
    limiter = AdapterRateLimiter({}, redis=fakeredis.aioredis.FakeRedis())
    start = perf_counter()
    await limiter.acquire("bar")
    elapsed = perf_counter() - start
    assert elapsed < 1
