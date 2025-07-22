"""Validation tests for mockup uploads."""

from __future__ import annotations

from fastapi.testclient import TestClient
import fakeredis.aioredis
from PIL import Image
from typing import Any
from pathlib import Path


def test_invalid_dimensions(monkeypatch: Any, tmp_path: Path) -> None:
    """Return 400 for mockups exceeding dimension limits."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    from marketplace_publisher.db import Marketplace
    from marketplace_publisher.main import app, rate_limiter
    from marketplace_publisher import publisher

    rate_limiter._redis = fakeredis.aioredis.FakeRedis()

    class DummyClient:
        def publish_design(self, design_path: Path, metadata: dict[str, Any]) -> str:
            return "1"

    publisher.CLIENTS[Marketplace.redbubble] = DummyClient()

    async def _noop(*args: Any, **kwargs: Any) -> None:
        return None

    publisher._fallback.publish = _noop

    with TestClient(app) as client:
        design = tmp_path / "bad.png"
        Image.new("RGB", (9001, 100)).save(design)
        response = client.post(
            "/publish",
            json={
                "marketplace": Marketplace.redbubble.value,
                "design_path": str(design),
                "metadata": {},
            },
        )
        assert response.status_code == 400
        assert "dimensions" in response.json()["detail"]
