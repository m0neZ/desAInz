"""Tests for aggregated system health endpoint."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, Optional, Type

import fakeredis.aioredis
import httpx
from fastapi.testclient import TestClient


sys.path.append(
    str(Path(__file__).resolve().parents[1] / "backend" / "api-gateway" / "src")
)
sys.path.append(
    str(Path(__file__).resolve().parents[1] / "backend" / "signal-ingestion" / "src")
)


def test_system_health(monkeypatch: Any) -> None:
    """All service health checks are aggregated successfully."""
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    import backend.shared.config as shared_config

    shared_config.settings.redis_url = "redis://localhost:6379/0"
    monkeypatch.setattr(
        "backend.shared.cache.get_async_client", lambda: fakeredis.aioredis.FakeRedis()
    )
    import api_gateway.main as main_module
    import api_gateway.routes as routes

    main_module.rate_limiter._redis = fakeredis.aioredis.FakeRedis()
    monkeypatch.setattr(
        "api_gateway.routes.get_async_client", lambda: fakeredis.aioredis.FakeRedis()
    )
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
            return httpx.Response(200, json={"status": "ok"})

    monkeypatch.setattr(httpx, "AsyncClient", MockClient)

    importlib.reload(main_module)
    importlib.reload(routes)

    client = TestClient(main_module.app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.headers["Cache-Control"].startswith("public")
    body = resp.json()
    for service in routes.HEALTH_ENDPOINTS:
        assert body[service] == "ok"
