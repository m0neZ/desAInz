"""Tests for the marketplace publisher API."""

from __future__ import annotations

from fastapi.testclient import TestClient
import fakeredis.aioredis


def test_publish_and_progress(monkeypatch, tmp_path) -> None:
    """Publish design and check initial progress."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    from marketplace_publisher.db import Marketplace
    from marketplace_publisher.main import app, rate_limiter
    from marketplace_publisher import publisher

    rate_limiter._redis = fakeredis.aioredis.FakeRedis()

    class DummyClient:
        def publish_design(self, design_path, metadata):
            return "1"

    publisher.CLIENTS[Marketplace.redbubble] = DummyClient()
    publisher._fallback.publish = lambda *args, **kwargs: None  # type: ignore

    with TestClient(app) as client:
        design = tmp_path / "a.png"
        design.write_text("img")
        response = client.post(
            "/publish",
            json={
                "marketplace": Marketplace.redbubble.value,
                "design_path": str(design),
                "metadata": {"title": "t"},
            },
        )
        assert response.status_code == 200
        task_id = response.json()["task_id"]

        response = client.get(f"/progress/{task_id}")
        assert response.status_code == 200
        assert response.json()["status"] in {
            "pending",
            "in_progress",
            "success",
            "failed",
        }
