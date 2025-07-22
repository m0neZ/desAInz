"""Adapter tests with VCR recordings."""

from __future__ import annotations

import os
import sys
import warnings
import asyncio
from types import TracebackType
import types
from typing import cast, Generator
import pytest
import fakeredis.aioredis
import fakeredis

from backend.shared import cache
import vcr

warnings.filterwarnings("ignore", category=ResourceWarning)
import httpx
import respx

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)


class AsyncFakeRedis:
    """Simplistic async Redis replacement."""

    def __init__(self) -> None:
        self.store: dict[str, int | str] = {}

    async def get(self, key: str) -> str | None:
        return cast(str | None, self.store.get(key))

    async def set(self, key: str, value: str) -> None:
        self.store[key] = value

    async def setex(self, key: str, ttl: int, value: str) -> None:
        self.store[key] = value

    async def decr(self, key: str) -> None:
        self.store[key] = int(self.store.get(key, 0)) - 1

    async def delete(self, key: str) -> None:
        self.store.pop(key, None)

    class _Pipe:
        def __init__(self, parent: "AsyncFakeRedis") -> None:
            self.parent = parent
            self.cmds: list[tuple[str, str, str | int]] = []

        async def __aenter__(self) -> "AsyncFakeRedis._Pipe":
            return self

        async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

        async def watch(self, key: str) -> None:  # noqa: D401
            return None

        async def get(self, key: str) -> str | None:
            return await self.parent.get(key)

        def multi(self) -> None:  # noqa: D401
            self.cmds.clear()

        def set(self, key: str, value: str, ex: int | None = None) -> None:
            self.cmds.append(("set", key, value))

        def decr(self, key: str) -> None:
            self.cmds.append(("decr", key, 0))

        async def execute(self) -> None:
            for op, key, val in self.cmds:
                if op == "set":
                    await self.parent.set(key, cast(str, val))
                elif op == "decr":
                    await self.parent.decr(key)

        async def unwatch(self) -> None:
            return None

    def pipeline(self) -> "AsyncFakeRedis._Pipe":
        return AsyncFakeRedis._Pipe(self)

    async def aclose(self) -> None:
        return None


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


@pytest.fixture(autouse=True)  # type: ignore[misc]
def _fake_redis(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Provide fakeredis clients to the adapters."""
    fake_sync = fakeredis.FakeRedis()
    fake_async = AsyncFakeRedis()
    monkeypatch.setattr(cache, "get_sync_client", lambda: fake_sync)
    monkeypatch.setattr(cache, "get_async_client", lambda: fake_async)
    import signal_ingestion.rate_limit as rl

    monkeypatch.setattr(rl, "get_async_client", lambda: fake_async)
    sys.modules["signal_ingestion.dedup"] = types.SimpleNamespace(  # type: ignore[assignment]
        redis_client=fake_sync,
        initialize=lambda *a, **k: None,
        is_duplicate=lambda k: False,
        add_key=lambda k: None,
    )
    yield
    fake_sync.close()
    asyncio.run(fake_async.aclose())


@pytest.mark.parametrize("adapter_cls, name", ADAPTERS)  # type: ignore[misc]
@pytest.mark.asyncio()  # type: ignore[misc]
async def test_fetch(
    adapter_cls: type[BaseAdapter], name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each adapter should invoke its HTTP layer and return data."""
    adapter = adapter_cls()

    async def fake_request(
        path: str, *args: object, **kwargs: object
    ) -> httpx.Response:
        request = httpx.Request("GET", path)
        if name == "instagram":
            response = httpx.Response(400, request=request)
            response.raise_for_status()
            return response
        if name == "reddit":
            return httpx.Response(
                200,
                json={
                    "data": {
                        "children": [
                            {
                                "data": {
                                    "id": "1",
                                    "title": "foo",
                                    "permalink": "/r/python",
                                }
                            }
                        ]
                    }
                },
                request=request,
            )
        if name == "youtube":
            if path.startswith("/youtube"):
                return httpx.Response(
                    200, json={"items": [{"id": "a"}]}, request=request
                )
            return httpx.Response(
                200, json={"title": "v", "html": "", "author_url": ""}, request=request
            )
        if name == "events":
            return httpx.Response(
                200, json=[{"date": "2025-01-01", "name": "Holiday"}], request=request
            )
        if name == "nostalgia":
            return httpx.Response(
                200,
                json={"response": {"docs": [{"identifier": "x", "title": "old"}]}},
                request=request,
            )
        return httpx.Response(200, json={"title": "t"}, request=request)

    monkeypatch.setattr(adapter, "_request", fake_request)

    if name == "instagram":
        with pytest.raises(httpx.HTTPStatusError):
            await adapter.fetch()
        return

    rows = await adapter.fetch()
    assert len(rows) >= 1
    assert isinstance(rows[0], dict)


class _DummyAdapter(TikTokAdapter):  # type: ignore[misc]
    """Dummy adapter subclass for testing."""


@pytest.mark.asyncio()  # type: ignore[misc]
async def test_custom_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure the adapter enforces the configured rate limit."""
    BaseAdapter._limiters.clear()

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
    BaseAdapter._limiters.clear()

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


@pytest.fixture()  # type: ignore[misc]
def _redis_with_dedup(monkeypatch: pytest.MonkeyPatch) -> Generator[object, None, None]:
    """Provide fakeredis with real dedup module."""

    class RedisWithTTL(fakeredis.FakeRedis):  # type: ignore[misc]
        """Fakeredis client with expiration support."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(*args, **kwargs)
            self.decode_responses = True

    fake_sync = RedisWithTTL()
    fake_async = fakeredis.aioredis.FakeRedis()
    monkeypatch.setattr(cache, "get_sync_client", lambda: fake_sync)
    monkeypatch.setattr(cache, "get_async_client", lambda: fake_async)
    import signal_ingestion.rate_limit as rl

    monkeypatch.setattr(rl, "get_async_client", lambda: fake_async)
    sys.modules.pop("signal_ingestion.dedup", None)
    import importlib

    dedup = importlib.import_module("signal_ingestion.dedup")
    dedup.redis_client = fake_sync  # type: ignore[attr-defined]
    dedup.initialize(5)
    yield dedup
    fake_sync.close()
    asyncio.run(fake_async.aclose())


class _ErrorAdapter(BaseAdapter):  # type: ignore[misc]
    """Adapter used solely for error handling tests."""

    async def fetch(self) -> list[dict[str, object]]:
        return []


@respx.mock  # type: ignore[misc]
@pytest.mark.asyncio()  # type: ignore[misc]
async def test_request_non_200(monkeypatch: pytest.MonkeyPatch) -> None:
    """``_request`` should raise for non-successful responses."""
    BaseAdapter._limiters.clear()
    respx.get("https://example.com/fail").respond(status_code=500)
    adapter = _ErrorAdapter(base_url="https://example.com", rate_limit=1)
    with pytest.raises(httpx.HTTPStatusError):
        await adapter._request("/fail")


@respx.mock  # type: ignore[misc]
@pytest.mark.asyncio()  # type: ignore[misc]
async def test_dedup_persists_on_error(
    _redis_with_dedup: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Deduplication cache continues to work when requests fail."""
    BaseAdapter._limiters.clear()
    import signal_ingestion.dedup as dedup

    dedup.add_key("existing")
    assert dedup.is_duplicate("existing")

    respx.get("https://example.com/fail").respond(status_code=500)
    adapter = _ErrorAdapter(base_url="https://example.com", rate_limit=1)

    with pytest.raises(httpx.HTTPStatusError):
        await adapter._request("/fail")

    assert dedup.is_duplicate("existing")
    dedup.add_key("new")
    assert dedup.is_duplicate("new")


@pytest.mark.asyncio()  # type: ignore[misc]
async def test_request_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    """``_request`` retries failed requests."""
    BaseAdapter._limiters.clear()
    calls: list[int] = []

    class DummyClient:
        def __init__(self, *a: object, **k: object) -> None:  # noqa: D401
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
            calls.append(1)
            if len(calls) == 1:
                raise httpx.ConnectError("fail", request=httpx.Request("GET", url))
            return httpx.Response(200, json={}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "AsyncClient", DummyClient)

    adapter = _ErrorAdapter(base_url="https://example.com", retries=2)
    resp = await adapter._request("/ok")

    assert resp.status_code == 200
    assert len(calls) == 2
