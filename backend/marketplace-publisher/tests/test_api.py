"""Tests for the marketplace publisher API."""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import fakeredis.aioredis
from fastapi.testclient import TestClient


def test_publish_and_progress(monkeypatch: Any, tmp_path: Path) -> None:
    """Publish design and check initial progress."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("SELENIUM_SKIP", "1")
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from marketplace_publisher import publisher
    from marketplace_publisher.db import Marketplace
    from marketplace_publisher.main import app, rate_limiter

    rate_limiter._redis = fakeredis.aioredis.FakeRedis()

    class DummyClient:
        def publish_design(self, design_path: Path, metadata: dict[str, Any]) -> str:
            assert "price" in metadata
            assert metadata["price"] > 0
            return "1"

    publisher.CLIENTS[Marketplace.redbubble] = DummyClient()

    async def _noop(*args: Any, **kwargs: Any) -> None:
        return None

    publisher._fallback.publish = _noop

    with TestClient(app) as client:
        design = tmp_path / "a.png"
        design.write_text("img")
        response = client.post(
            "/publish",
            json={
                "marketplace": Marketplace.redbubble.value,
                "design_path": str(design),
                "score": 1.0,
                "metadata": {"title": "t"},
            },
        )
        assert response.status_code == 200
        task_id = response.json()["task_id"]

        response = client.get(f"/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["status"] in {
            "pending",
            "in_progress",
            "success",
            "failed",
        }
