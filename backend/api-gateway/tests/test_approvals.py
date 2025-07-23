"""Tests for approval endpoints."""

import importlib
import sys
from pathlib import Path

import fakeredis.aioredis
from fastapi.testclient import TestClient
from api_gateway.auth import create_access_token

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402


def test_approval_flow(monkeypatch):
    """Approve a run and check status."""
    import api_gateway.main as main_module
    import api_gateway.routes as routes

    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    import backend.shared.config as shared_config

    shared_config.settings.redis_url = "redis://localhost:6379/0"
    monkeypatch.setattr(
        "backend.shared.cache.get_async_client", lambda: fakeredis.aioredis.FakeRedis()
    )
    importlib.reload(main_module)
    importlib.reload(routes)

    main_module.rate_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.optimization_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.monitoring_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.analytics_limiter._redis = fakeredis.aioredis.FakeRedis()

    client = TestClient(main_module.app)
    token = create_access_token({"sub": "admin"})
    run_id = "run123"
    resp = client.post(
        f"/approvals/{run_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    resp = client.get(f"/approvals/{run_id}")
    assert resp.status_code == 200
    assert resp.json() == {"approved": True}


def test_list_pending_runs(monkeypatch):
    """Return run IDs awaiting approval."""
    import api_gateway.main as main_module
    import api_gateway.routes as routes

    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    import backend.shared.config as shared_config

    shared_config.settings.redis_url = "redis://localhost:6379/0"
    redis_client = fakeredis.aioredis.FakeRedis()
    monkeypatch.setattr("backend.shared.cache.get_async_client", lambda: redis_client)
    importlib.reload(main_module)
    importlib.reload(routes)

    main_module.rate_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.optimization_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.monitoring_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.analytics_limiter._redis = fakeredis.aioredis.FakeRedis()

    client = TestClient(main_module.app)
    redis_client.sadd("pending_runs", "run123")
    resp = client.get("/approvals")
    assert resp.status_code == 200
    assert resp.json() == {"runs": ["run123"]}


def test_reject_run(monkeypatch):
    """Reject a run and ensure it is removed from pending."""
    import api_gateway.main as main_module
    import api_gateway.routes as routes

    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    import backend.shared.config as shared_config

    shared_config.settings.redis_url = "redis://localhost:6379/0"
    redis_client = fakeredis.aioredis.FakeRedis()
    monkeypatch.setattr("backend.shared.cache.get_async_client", lambda: redis_client)
    importlib.reload(main_module)
    importlib.reload(routes)

    main_module.rate_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.optimization_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.monitoring_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.analytics_limiter._redis = fakeredis.aioredis.FakeRedis()

    client = TestClient(main_module.app)
    token = create_access_token({"sub": "admin"})
    run_id = "run123"
    redis_client.sadd("pending_runs", run_id)
    resp = client.delete(
        f"/approvals/{run_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "rejected"}
    assert not redis_client.sismember("pending_runs", run_id)
