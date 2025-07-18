"""Feature flag tests for marketplace publisher."""

from __future__ import annotations

from fastapi.testclient import TestClient
import fakeredis.aioredis
from typing import Any
from pathlib import Path


def test_society6_flag(monkeypatch: Any, tmp_path: Path) -> None:
    """Return 403 when Society6 integration is disabled."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    from marketplace_publisher.db import Marketplace
    from marketplace_publisher.main import app, rate_limiter
    from marketplace_publisher import publisher
    from backend.shared import feature_flags

    rate_limiter._redis = fakeredis.aioredis.FakeRedis()
    feature_flags.initialize()

    class DummyClient:
        def publish_design(self, design_path: Path, metadata: dict[str, Any]) -> str:
            return "1"

    publisher.CLIENTS[Marketplace.society6] = DummyClient()  # type: ignore[assignment]
    publisher._fallback.publish = lambda *args, **kwargs: None  # type: ignore

    with TestClient(app) as client:
        design = tmp_path / "a.png"
        design.write_text("img")
        response = client.post(
            "/publish",
            json={
                "marketplace": Marketplace.society6.value,
                "design_path": str(design),
                "metadata": {},
            },
        )
        assert response.status_code == 403


def test_zazzle_flag(monkeypatch: Any, tmp_path: Path) -> None:
    """Return 403 when Zazzle integration is disabled."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    from marketplace_publisher.db import Marketplace
    from marketplace_publisher.main import app, rate_limiter
    from marketplace_publisher import publisher
    from backend.shared import feature_flags

    rate_limiter._redis = fakeredis.aioredis.FakeRedis()
    feature_flags.initialize()

    class DummyClient:
        def publish_design(self, design_path: Path, metadata: dict[str, Any]) -> str:
            return "1"

    publisher.CLIENTS[Marketplace.zazzle] = DummyClient()  # type: ignore[assignment]
    publisher._fallback.publish = lambda *args, **kwargs: None  # type: ignore

    with TestClient(app) as client:
        design = tmp_path / "a.png"
        design.write_text("img")
        response = client.post(
            "/publish",
            json={
                "marketplace": Marketplace.zazzle.value,
                "design_path": str(design),
                "metadata": {},
            },
        )
        assert response.status_code == 403
