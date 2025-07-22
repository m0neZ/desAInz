"""Rate limit tests for the publisher service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import fakeredis.aioredis
from fastapi.testclient import TestClient


def test_rate_limit_exceeded(monkeypatch: Any, tmp_path: Path) -> None:
    """Return 429 when requests exceed the allowed rate."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("RATE_LIMIT_REDBUBBLE", "1")
    from marketplace_publisher import publisher
    from marketplace_publisher.db import Marketplace
    from marketplace_publisher.main import app, rate_limiter

    rate_limiter._redis = fakeredis.aioredis.FakeRedis()
    rate_limiter._limits[Marketplace.redbubble] = 1  # type: ignore[index]

    class DummyClient:
        def publish_design(self, design_path: Path, metadata: dict[str, Any]) -> str:
            return "1"

    publisher.CLIENTS[Marketplace.redbubble] = DummyClient()

    async def _noop(*args: Any, **kwargs: Any) -> None:
        return None

    publisher._fallback.publish = _noop

    with TestClient(app) as client:
        design = tmp_path / "a.png"
        design.write_text("img")
        resp1 = client.post(
            "/publish",
            json={
                "marketplace": Marketplace.redbubble.value,
                "design_path": str(design),
                "metadata": {},
            },
        )
        assert resp1.status_code == 200
        resp2 = client.post(
            "/publish",
            json={
                "marketplace": Marketplace.redbubble.value,
                "design_path": str(design),
                "metadata": {},
            },
        )
        assert resp2.status_code == 429
