from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, Optional, Type

import httpx
from fastapi.testclient import TestClient
import fakeredis.aioredis

sys.path.append(
    str(Path(__file__).resolve().parents[1] / "backend" / "api-gateway" / "src")
)


def test_trending_proxy(monkeypatch: Any) -> None:
    monkeypatch.setenv("SIGNAL_INGESTION_URL", "http://ingest:1234")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    import backend.shared.config as shared_config

    shared_config.settings.redis_url = "redis://localhost:6379/0"
    monkeypatch.setattr(
        "backend.shared.cache.get_async_client", lambda: fakeredis.aioredis.FakeRedis()
    )
    import api_gateway.main as main_module
    import api_gateway.routes as routes

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
            assert url == "http://ingest:1234/trending?limit=5"
            return httpx.Response(200, json=["foo", "bar"])

    monkeypatch.setattr(httpx, "AsyncClient", MockClient)
    importlib.reload(routes)
    client = TestClient(main_module.app)

    resp = client.get("/trending?limit=5")
    assert resp.status_code == 200
    assert resp.json() == ["foo", "bar"]
