"""Tests for request rate limiting middleware."""

import importlib
import sys
from pathlib import Path
from typing import Any

import fakeredis.aioredis
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402
sys.path.append(
    str(Path(__file__).resolve().parents[2] / "mockup-generation")
)  # noqa: E402

import api_gateway.main as main_module  # noqa: E402


def test_rate_limit_exceeded(monkeypatch: Any) -> None:
    """Return 429 when requests exceed the per-user limit."""
    monkeypatch.setenv("RATE_LIMIT_PER_USER", "1")
    importlib.reload(main_module)
    main_module.rate_limiter._redis = fakeredis.aioredis.FakeRedis()

    client = TestClient(main_module.app)
    resp1 = client.get("/status")
    assert resp1.status_code == 200
    resp2 = client.get("/status")
    assert resp2.status_code == 429
