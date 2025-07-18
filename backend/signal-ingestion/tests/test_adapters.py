"""Adapter tests with VCR recordings."""

from __future__ import annotations

import os
import sys
import asyncio
from types import TracebackType
from typing import cast
import pytest
import vcr
import httpx

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from signal_ingestion.adapters.events import EventsAdapter  # noqa: E402
from signal_ingestion.adapters.instagram import InstagramAdapter  # noqa: E402
from signal_ingestion.adapters.nostalgia import NostalgiaAdapter  # noqa: E402
from signal_ingestion.adapters.reddit import RedditAdapter  # noqa: E402
from signal_ingestion.adapters.tiktok import TikTokAdapter  # noqa: E402
from signal_ingestion.adapters.youtube import YouTubeAdapter  # noqa: E402
from signal_ingestion.adapters.base import BaseAdapter  # noqa: E402

ADAPTERS = [
    (TikTokAdapter, "tiktok"),
    (InstagramAdapter, "instagram"),
    (RedditAdapter, "reddit"),
    (YouTubeAdapter, "youtube"),
    (EventsAdapter, "events"),
    (NostalgiaAdapter, "nostalgia"),
]


@pytest.mark.parametrize("adapter_cls, name", ADAPTERS)  # type: ignore[misc]
@pytest.mark.asyncio()  # type: ignore[misc]
async def test_fetch(adapter_cls: type[BaseAdapter], name: str) -> None:
    """Each adapter should fetch one item."""
    adapter = adapter_cls()  # type: ignore[call-arg]
    cassette = f"backend/signal-ingestion/tests/cassettes/{name}.yaml"
    with vcr.use_cassette(cassette, record_mode="new_episodes"):
        if name == "instagram":
            with pytest.raises(httpx.HTTPStatusError):
                await adapter.fetch()
            return
        rows = await adapter.fetch()
    assert len(rows) == 1
    assert isinstance(rows[0], dict)


class _DummyAdapter(TikTokAdapter):  # type: ignore[misc]
    """Dummy adapter subclass for testing."""


@pytest.mark.asyncio()  # type: ignore[misc]
async def test_custom_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure the adapter enforces the configured rate limit."""
    BaseAdapter._semaphores.clear()

    order: list[str] = []

    class DummyClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        async def __aenter__(self) -> "DummyClient":
            return self

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> None:
            pass

        async def get(
            self, url: str, headers: dict[str, str] | None = None
        ) -> httpx.Response:
            order.append("start")
            await asyncio.sleep(0.01)
            order.append("end")
            request = httpx.Request("GET", url)
            return httpx.Response(200, json={}, request=request)

    monkeypatch.setattr(httpx, "AsyncClient", DummyClient)

    adapter = _DummyAdapter(base_url="https://example.com", rate_limit=1)
    await asyncio.gather(adapter._request("/a"), adapter._request("/b"))

    assert order == ["start", "end", "start", "end"]


@pytest.mark.asyncio()  # type: ignore[misc]
async def test_proxy_rotation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adapters rotate through configured proxies."""
    BaseAdapter._semaphores.clear()

    used: list[str | None] = []

    class DummyClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            used.append(cast(str | None, kwargs.get("proxy")))

        async def __aenter__(self) -> "DummyClient":
            return self

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> None:
            pass

        async def get(
            self, url: str, headers: dict[str, str] | None = None
        ) -> httpx.Response:
            request = httpx.Request("GET", url)
            return httpx.Response(200, json={}, request=request)

    monkeypatch.setattr(httpx, "AsyncClient", DummyClient)

    adapter = _DummyAdapter(
        base_url="https://example.com",
        proxies=["http://proxy1", "http://proxy2"],
        rate_limit=1,
    )
    await adapter._request("/a")
    await adapter._request("/b")

    assert used == ["http://proxy1", "http://proxy2"]
