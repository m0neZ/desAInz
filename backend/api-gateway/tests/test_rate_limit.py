"""Tests for request rate limiting middleware."""

import importlib
import sys
from pathlib import Path
from typing import Any
import warnings
import asyncio

import fakeredis.aioredis
from fastapi.testclient import TestClient
from pydantic import RedisDsn
from backend.shared import metrics
import prometheus_client

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402
sys.path.append(
    str(Path(__file__).resolve().parents[2] / "mockup-generation")
)  # noqa: E402


def test_rate_limit_exceeded(monkeypatch: Any) -> None:
    """Return 429 when requests exceed the per-user limit."""
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=ResourceWarning)
    warnings.filterwarnings("ignore", category=ResourceWarning)
    monkeypatch.setenv("RATE_LIMIT_PER_USER", "1")
    monkeypatch.setenv("API_GATEWAY_REQUEST_CACHE_TTL", "1")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    import api_gateway.main as main_module
    import backend.shared.config as shared_config

    shared_config.settings.redis_url = RedisDsn("redis://localhost:6379/0")
    importlib.reload(main_module)
    redis = fakeredis.aioredis.FakeRedis()
    main_module.rate_limiter._redis = redis

    client = TestClient(main_module.app)
    resp1 = client.get("/status")
    assert resp1.status_code == 200
    resp2 = client.get("/status")
    assert resp2.status_code == 429
    asyncio.run(redis.aclose())


def test_rate_limit_metrics_increment(monkeypatch: Any) -> None:
    """Rate limiter updates Prometheus counters when limit exceeded."""
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    monkeypatch.setenv("API_GATEWAY_REQUEST_CACHE_TTL", "1")
    monkeypatch.setenv("RATE_LIMIT_PER_USER", "1")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    import api_gateway.main as main_module
    import backend.shared.config as shared_config

    shared_config.settings.redis_url = RedisDsn("redis://localhost:6379/0")
    redis = fakeredis.aioredis.FakeRedis()
    monkeypatch.setattr("backend.shared.cache.get_async_client", lambda: redis)
    if hasattr(main_module, "REQUEST_LATENCY"):
        prometheus_client.REGISTRY.unregister(main_module.REQUEST_LATENCY)
        prometheus_client.REGISTRY.unregister(main_module.ERROR_COUNTER)
    importlib.reload(main_module)
    main_module.rate_limiter._redis = redis
    client = TestClient(main_module.app)
    registry = prometheus_client.REGISTRY
    latency_name = "api_gateway_request_latency_seconds_count"
    counter_name = "http_requests_total"
    labels = {"method": "GET", "endpoint": "/status"}
    before_latency = registry.get_sample_value(latency_name, labels) or 0.0
    before_counter = registry.get_sample_value(counter_name, labels) or 0.0
    resp1 = client.get("/status")
    assert resp1.status_code == 200
    metrics._flush_metrics()
    resp2 = client.get("/status")
    assert resp2.status_code == 429
    metrics._flush_metrics()
    asyncio.run(redis.aclose())
    after_latency = registry.get_sample_value(latency_name, labels)
    after_counter = registry.get_sample_value(counter_name, labels)
    assert after_latency and after_latency > before_latency
    assert after_counter and after_counter > before_counter
