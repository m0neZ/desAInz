"""Tests for ETag caching in the base adapter."""

from __future__ import annotations

import os
import sys
from typing import Any, Generator

import fakeredis.aioredis
import httpx
import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from backend.shared import cache  # noqa: E402
from backend.shared.config import settings as shared_settings  # noqa: E402
import signal_ingestion.rate_limit as rl  # noqa: E402
import warnings
from signal_ingestion.adapters.base import BaseAdapter  # noqa: E402


warnings.filterwarnings("ignore", category=DeprecationWarning, module="redis.*")


@pytest.fixture(autouse=True)  # type: ignore[misc]
def _fake_redis(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Provide a fake Redis client."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(cache, "get_async_client", lambda: fake)
    monkeypatch.setattr(rl, "get_async_client", lambda: fake)
    monkeypatch.setattr(shared_settings, "redis_url", "redis://localhost:6379/0")
    yield
    import asyncio

    asyncio.get_event_loop().run_until_complete(fake.aclose())


@pytest.mark.asyncio()  # type: ignore[misc]
async def test_etag_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Store and send ETag headers for subsequent requests."""

    calls: list[dict[str, str]] = []

    class DummyClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> "DummyClient":
            return self

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: object | None,
        ) -> None:
            pass

        async def get(
            self, url: str, headers: dict[str, str] | None = None
        ) -> httpx.Response:
            calls.append(headers or {})
            request = httpx.Request("GET", url)
            if len(calls) == 1:
                return httpx.Response(
                    200, json={}, headers={"ETag": "v1"}, request=request
                )
            return httpx.Response(304, request=request)

    monkeypatch.setattr(httpx, "AsyncClient", DummyClient)

    adapter = BaseAdapter(base_url="https://example.com")

    first = await adapter._request("/a")
    assert first is not None
    client = cache.get_async_client()
    stored = await client.get("etag:https://example.com/a")
    assert (stored.decode() if isinstance(stored, bytes) else stored) == "v1"

    second = await adapter._request("/a")
    assert second is None
    assert calls[1].get("If-None-Match") == "v1"
