"""Tests for Prometheus metrics instrumentation."""

import importlib
import sys
from pathlib import Path
from typing import Any

import fakeredis.aioredis
import prometheus_client
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402


def test_metrics_latency_increment(monkeypatch: Any) -> None:
    """Latency histogram increments after a request."""
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    import backend.shared.config as shared_config

    shared_config.settings.redis_url = "redis://localhost:6379/0"
    monkeypatch.setattr(
        "backend.shared.cache.get_async_client", lambda: fakeredis.aioredis.FakeRedis()
    )
    import api_gateway.main as main_module

    if hasattr(main_module, "REQUEST_LATENCY"):
        prometheus_client.REGISTRY.unregister(main_module.REQUEST_LATENCY)
        prometheus_client.REGISTRY.unregister(main_module.ERROR_COUNTER)

    importlib.reload(main_module)
    main_module.rate_limiter._redis = fakeredis.aioredis.FakeRedis()
    client = TestClient(main_module.app)
    registry = prometheus_client.REGISTRY
    sample_name = "api_gateway_request_latency_seconds_count"
    labels = {"method": "GET", "endpoint": "/health"}
    before = registry.get_sample_value(sample_name, labels) or 0.0
    resp = client.get("/health")
    assert resp.status_code == 200
    after = registry.get_sample_value(sample_name, labels)
    assert after == before + 1.0
