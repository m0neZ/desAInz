"""Tests for ETag caching of tRPC proxy."""

from __future__ import annotations

import importlib
import asyncio
from pathlib import Path
from types import TracebackType
from typing import Any, Optional, Type

import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

import fakeredis.aioredis
import httpx
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _setup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    import backend.shared.config as shared_config

    shared_config.settings.redis_url = "redis://localhost:6379/0"
    monkeypatch.setattr(
        "backend.shared.cache.get_async_client", lambda: fakeredis.aioredis.FakeRedis()
    )
    import warnings

    warnings.filterwarnings("ignore", category=DeprecationWarning)
    import api_gateway.main as main_module

    if hasattr(main_module, "REQUEST_LATENCY"):
        import prometheus_client

        prometheus_client.REGISTRY.unregister(main_module.REQUEST_LATENCY)
        prometheus_client.REGISTRY.unregister(main_module.ERROR_COUNTER)

    importlib.reload(main_module)
    import api_gateway.routes as routes

    main_module.rate_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.optimization_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.monitoring_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.analytics_limiter._redis = fakeredis.aioredis.FakeRedis()


def test_trpc_etag(monkeypatch: pytest.MonkeyPatch) -> None:
    """Proxy tRPC call respecting ETag caching."""
    from api_gateway.auth import create_access_token
    import api_gateway.main as main_module
    import api_gateway.routes as routes

    client = TestClient(main_module.app)
    token = create_access_token({"sub": "tester"})
    calls: list[dict[str, str] | None] = []

    class MockClient:
        async def __aenter__(self) -> "MockClient":
            return self

        async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc: Optional[BaseException],
            tb: Optional[TracebackType],
        ) -> None:
            return None

        async def post(
            self,
            url: str,
            json: Any | None = None,
            headers: dict[str, str] | None = None,
        ) -> httpx.Response:
            calls.append(headers)
            request = httpx.Request("POST", url)
            if len(calls) == 1:
                return httpx.Response(
                    200,
                    json={"result": {"message": "pong", "user": "tester"}},
                    headers={"ETag": "v1"},
                    request=request,
                )
            return httpx.Response(304, request=request)

    monkeypatch.setattr("api_gateway.routes.TRPC_SERVICE_URL", "http://backend:8000")
    monkeypatch.setattr(httpx, "AsyncClient", MockClient)

    first = client.post("/trpc/ping", headers={"Authorization": f"Bearer {token}"})
    assert first.status_code == 200
    assert first.headers["ETag"] == "v1"
    assert first.json()["result"]["message"] == "pong"

    second = client.post("/trpc/ping", headers={"Authorization": f"Bearer {token}"})
    assert second.status_code == 304
    assert second.text == ""
    assert calls[1].get("If-None-Match") == "v1"

    redis = routes.get_async_client()
    stored = asyncio.get_event_loop().run_until_complete(redis.get("etag:trpc:ping"))
    assert (stored.decode() if isinstance(stored, bytes) else stored) == "v1"
