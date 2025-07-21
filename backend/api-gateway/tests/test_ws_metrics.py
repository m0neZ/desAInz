"""Tests for /ws/metrics endpoint."""

import asyncio
import importlib
import sys
from pathlib import Path
from typing import Any, Optional, Type
import warnings

import fakeredis.aioredis
import httpx
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402
sys.path.append(
    str(Path(__file__).resolve().parents[2] / "signal-ingestion" / "src")
)  # noqa: E402


def test_metrics_ws(monkeypatch: Any) -> None:
    """Endpoint streams combined metrics."""
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("API_GATEWAY_WS_INTERVAL_MS", "1000")
    import backend.shared.config as shared_config

    shared_config.settings.redis_url = "redis://localhost:6379/0"
    monkeypatch.setattr(
        "backend.shared.cache.get_async_client", lambda: fakeredis.aioredis.FakeRedis()
    )
    import api_gateway.main as main_module
    import api_gateway.routes as routes

    if hasattr(main_module, "REQUEST_LATENCY"):
        import prometheus_client

        prometheus_client.REGISTRY.unregister(main_module.REQUEST_LATENCY)
        prometheus_client.REGISTRY.unregister(main_module.ERROR_COUNTER)

    monkeypatch.setattr(
        "api_gateway.routes.get_async_client", lambda: fakeredis.aioredis.FakeRedis()
    )
    importlib.reload(main_module)
    importlib.reload(routes)
    main_module.rate_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.optimization_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.monitoring_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.analytics_limiter._redis = fakeredis.aioredis.FakeRedis()

    class MockClient:
        async def __aenter__(self) -> "MockClient":
            return self

        async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc: Optional[BaseException],
            tb: Optional[Type[BaseException]],
        ) -> None:
            return None

        async def get(self, url: str) -> httpx.Response:
            if url.endswith("/overview"):
                return httpx.Response(200, json={"cpu_percent": 1})
            if url.endswith("/analytics"):
                return httpx.Response(200, json={"active_users": 2})
            return httpx.Response(404)

    async def fake_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(httpx, "AsyncClient", MockClient)
    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    client = TestClient(main_module.app)
    with client.websocket_connect("/ws/metrics") as ws:
        interval = ws.receive_json()
        assert interval == {"interval_ms": 1000}
        data = ws.receive_json()
        assert data == {"cpu_percent": 1, "active_users": 2}
