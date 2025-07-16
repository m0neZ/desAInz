"""Tests for the marketplace publisher API."""

from __future__ import annotations

from fastapi.testclient import TestClient
import fakeredis.aioredis
from typing import Any
from pathlib import Path


def test_publish_and_progress(monkeypatch: Any, tmp_path: Path) -> None:
    """Publish design and check initial progress."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    from marketplace_publisher.db import Marketplace
    from marketplace_publisher.main import app, rate_limiter
    from marketplace_publisher import publisher

    rate_limiter._redis = fakeredis.aioredis.FakeRedis()

    class DummyClient:
        def publish_design(self, design_path: Path, metadata: dict[str, Any]) -> str:
            return "1"

    publisher.CLIENTS[Marketplace.redbubble] = DummyClient()  # type: ignore[assignment]
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


def test_shopify_flag(monkeypatch: Any, tmp_path: Path) -> None:
    """Allow publishing to Shopify only when the feature flag is enabled."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    from marketplace_publisher.db import Marketplace
    from marketplace_publisher.main import app, rate_limiter
    from marketplace_publisher import publisher

    rate_limiter._redis = fakeredis.aioredis.FakeRedis()

    class DummyClient:
        def publish_design(self, design_path: Path, metadata: dict[str, Any]) -> str:
            return "1"

    publisher.CLIENTS[Marketplace.shopify] = DummyClient()  # type: ignore[assignment]
    publisher._fallback.publish = lambda *args, **kwargs: None  # type: ignore

    with TestClient(app) as client:
        design = tmp_path / "a.png"
        design.write_text("img")

        monkeypatch.setattr("marketplace_publisher.main.is_enabled", lambda flag: False)
        response = client.post(
            "/publish",
            json={
                "marketplace": Marketplace.shopify.value,
                "design_path": str(design),
                "metadata": {},
            },
        )
        assert response.status_code == 403

        monkeypatch.setattr("marketplace_publisher.main.is_enabled", lambda flag: True)
        response = client.post(
            "/publish",
            json={
                "marketplace": Marketplace.shopify.value,
                "design_path": str(design),
                "metadata": {},
            },
        )
        assert response.status_code == 200
