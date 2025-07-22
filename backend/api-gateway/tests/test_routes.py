"""Tests for routing logic."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402
sys.path.append(
    str(Path(__file__).resolve().parents[2] / "signal-ingestion" / "src")
)  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402
import httpx  # noqa: E402
import pytest  # noqa: E402

from types import TracebackType  # noqa: E402
from typing import Any, Optional, Type  # noqa: E402


def test_status(monkeypatch: pytest.MonkeyPatch) -> None:
    """Status endpoint should return OK."""
    import importlib
    import fakeredis.aioredis

    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    import backend.shared.config as shared_config

    shared_config.settings.redis_url = "redis://localhost:6379/0"
    import api_gateway.main as main_module

    import api_gateway.routes as routes

    main_module.rate_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.optimization_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.monitoring_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.analytics_limiter._redis = fakeredis.aioredis.FakeRedis()

    client = TestClient(main_module.app)

    response = client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


import pytest  # noqa: E402


def test_trpc_ping(monkeypatch: pytest.MonkeyPatch) -> None:
    """Proxy tRPC ping to backend service."""
    import importlib
    import fakeredis.aioredis

    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    import backend.shared.config as shared_config

    shared_config.settings.redis_url = "redis://localhost:6379/0"
    import api_gateway.main as main_module
    import api_gateway.routes as routes

    main_module.rate_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.optimization_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.monitoring_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.analytics_limiter._redis = fakeredis.aioredis.FakeRedis()
    from api_gateway.auth import create_access_token

    client = TestClient(main_module.app)

    token = create_access_token({"sub": "tester"})

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
            assert url.endswith("/trpc/ping")
            assert headers == {"Authorization": f"Bearer {token}"}
            return httpx.Response(
                200,
                json={"result": {"message": "pong", "user": "tester"}},
            )

    monkeypatch.setattr("api_gateway.routes.TRPC_SERVICE_URL", "http://backend:8000")
    monkeypatch.setattr(httpx, "AsyncClient", MockClient)
    response = client.post(
        "/trpc/ping",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["result"]["message"] == "pong"
    assert body["result"]["user"] == "tester"


def test_trpc_etag(monkeypatch: pytest.MonkeyPatch) -> None:
    """TRPC endpoint should respond with 304 when ETag matches."""
    import importlib
    import warnings
    import fakeredis.aioredis
    import prometheus_client

    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    prometheus_client.REGISTRY = prometheus_client.CollectorRegistry()
    import backend.shared.config as shared_config

    shared_config.settings.redis_url = "redis://localhost:6379/0"
    import api_gateway.main as main_module
    import api_gateway.routes as routes

    main_module.rate_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.optimization_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.monitoring_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.analytics_limiter._redis = fakeredis.aioredis.FakeRedis()
    from api_gateway.auth import create_access_token

    client = TestClient(main_module.app)

    token = create_access_token({"sub": "tester"})

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
            assert url.endswith("/trpc/ping")
            assert headers is not None and "Authorization" in headers
            return httpx.Response(
                200,
                json={"result": {"message": "pong", "user": "tester"}},
            )

    monkeypatch.setattr("api_gateway.routes.TRPC_SERVICE_URL", "http://backend:8000")
    monkeypatch.setattr(httpx, "AsyncClient", MockClient)

    first = client.post("/trpc/ping", headers={"Authorization": f"Bearer {token}"})
    assert first.status_code == 200
    etag = first.headers["ETag"]

    second = client.post(
        "/trpc/ping",
        headers={"Authorization": f"Bearer {token}", "If-None-Match": etag},
    )
    assert second.status_code == 304
    assert second.headers["ETag"] == etag


def test_optimization_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Proxy optimization endpoint to optimization service."""
    import importlib
    import fakeredis.aioredis

    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setattr(
        "api_gateway.routes.get_async_client", lambda: fakeredis.aioredis.FakeRedis()
    )
    import api_gateway.main as main_module

    importlib.reload(main_module)
    from api_gateway.auth import create_access_token

    client = TestClient(main_module.app)

    token = create_access_token({"sub": "tester"})

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

        async def get(self, url: str) -> httpx.Response:
            assert url.endswith("/optimizations")
            return httpx.Response(200, json=["a", "b"])

    monkeypatch.setattr(httpx, "AsyncClient", MockClient)
    resp = client.get("/optimizations", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json() == ["a", "b"]


def test_monitoring_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Proxy monitoring endpoint."""
    import importlib
    import fakeredis.aioredis

    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    import backend.shared.config as shared_config

    shared_config.settings.redis_url = "redis://localhost:6379/0"
    import api_gateway.main as main_module

    importlib.reload(main_module)
    import api_gateway.routes as routes

    main_module.rate_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.optimization_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.monitoring_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.analytics_limiter._redis = fakeredis.aioredis.FakeRedis()

    client = TestClient(main_module.app)

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

        async def get(self, url: str) -> httpx.Response:
            assert url.endswith("/overview")
            return httpx.Response(200, json={"cpu": 1})

    monkeypatch.setattr(httpx, "AsyncClient", MockClient)
    resp = client.get("/monitoring/overview")
    assert resp.status_code == 200
    assert resp.json() == {"cpu": 1}


def test_analytics_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Proxy analytics endpoint."""
    import importlib
    import fakeredis.aioredis

    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    import backend.shared.config as shared_config

    shared_config.settings.redis_url = "redis://localhost:6379/0"
    import api_gateway.main as main_module

    importlib.reload(main_module)
    import api_gateway.routes as routes

    main_module.rate_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.optimization_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.monitoring_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.analytics_limiter._redis = fakeredis.aioredis.FakeRedis()

    client = TestClient(main_module.app)

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

        async def get(self, url: str) -> httpx.Response:
            assert url.endswith("/low_performers?limit=5&page=0")
            return httpx.Response(200, json=[{"id": 1}])

    monkeypatch.setattr(httpx, "AsyncClient", MockClient)
    resp = client.get("/analytics/low_performers?limit=5&page=0")
    assert resp.status_code == 200
    assert resp.json() == [{"id": 1}]
