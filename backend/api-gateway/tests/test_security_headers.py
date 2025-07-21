"""Security headers are added to all responses."""

import importlib
import sys
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
import fakeredis.aioredis
import warnings

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402


def test_security_headers(monkeypatch: Any) -> None:
    """Security headers are applied based on configuration."""
    monkeypatch.setenv("CONTENT_SECURITY_POLICY", "default-src 'self'")
    monkeypatch.setenv("HSTS", "max-age=3600")

    import backend.shared.config as shared_config

    importlib.reload(shared_config)
    shared_config.settings.content_security_policy = "default-src 'self'"
    shared_config.settings.hsts = "max-age=3600"
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setattr(
        "backend.shared.cache.get_async_client", lambda: fakeredis.aioredis.FakeRedis()
    )
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    import api_gateway.main as main_module

    if hasattr(main_module, "REQUEST_LATENCY"):
        import prometheus_client

        prometheus_client.REGISTRY.unregister(main_module.REQUEST_LATENCY)
        prometheus_client.REGISTRY.unregister(main_module.ERROR_COUNTER)

    importlib.reload(main_module)

    client = TestClient(main_module.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers["Content-Security-Policy"] == "default-src 'self'"
    assert resp.headers["Strict-Transport-Security"] == "max-age=3600"
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "same-origin"
