"""Tests for the marketplace publisher API."""

from __future__ import annotations

from fastapi.testclient import TestClient
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[3]))



def test_publish_and_progress(monkeypatch, tmp_path) -> None:
    """Publish design and check initial progress."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    from marketplace_publisher.db import Marketplace
    from marketplace_publisher.main import app, limiter
    import fakeredis
    from marketplace_publisher import db
    db.init_db = lambda: None  # type: ignore
    limiter._client = fakeredis.FakeRedis()
    from marketplace_publisher import publisher

    class DummyClient:
        def publish_design(self, design_path, metadata):
            return "1"

    publisher.CLIENTS[Marketplace.redbubble] = DummyClient()
    publisher._fallback.publish = lambda *args, **kwargs: None  # type: ignore

    with TestClient(app) as client:
        design = tmp_path / "a.png"
        design.write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc``\x00\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
        )
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


def test_publish_validation_error(monkeypatch, tmp_path) -> None:
    """Return 400 when validation fails."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    from marketplace_publisher.db import Marketplace
    from marketplace_publisher.main import app, limiter
    import fakeredis
    from marketplace_publisher import db
    db.init_db = lambda: None  # type: ignore
    limiter._client = fakeredis.FakeRedis()
    from marketplace_publisher import publisher, rules

    class DummyClient:
        def publish_design(self, design_path, metadata):
            return "1"

    rules.RULES[Marketplace.redbubble] = rules.MarketplaceRule(
        max_file_size=1,
        max_width=10,
        max_height=10,
        daily_upload_limit=1,
    )
    limiter.acquire = lambda *args, **kwargs: True  # type: ignore
    publisher.CLIENTS[Marketplace.redbubble] = DummyClient()
    publisher._fallback.publish = lambda *args, **kwargs: None  # type: ignore

    with TestClient(app) as client:
        design = tmp_path / "b.png"
        design.write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc``\x00\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        resp = client.post(
            "/publish",
            json={
                "marketplace": Marketplace.redbubble.value,
                "design_path": str(design),
                "metadata": {},
            },
        )
        assert resp.status_code == 400


def test_publish_rate_limit(monkeypatch, tmp_path) -> None:
    """Return 429 when exceeding rate limit."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    from marketplace_publisher.db import Marketplace
    from marketplace_publisher.main import app, limiter
    import fakeredis
    from marketplace_publisher import db
    db.init_db = lambda: None  # type: ignore
    limiter._client = fakeredis.FakeRedis()
    from marketplace_publisher import publisher, rules

    class DummyClient:
        def publish_design(self, design_path, metadata):
            return "1"

    rules.RULES[Marketplace.redbubble] = rules.MarketplaceRule(
        max_file_size=100,
        max_width=10,
        max_height=10,
        daily_upload_limit=1,
    )
    publisher.CLIENTS[Marketplace.redbubble] = DummyClient()
    publisher._fallback.publish = lambda *args, **kwargs: None  # type: ignore

    with TestClient(app) as client:
        design = tmp_path / "c.png"
        design.write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc``\x00\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        first = client.post(
            "/publish",
            json={
                "marketplace": Marketplace.redbubble.value,
                "design_path": str(design),
                "metadata": {},
            },
        )
        assert first.status_code == 200
        second = client.post(
            "/publish",
            json={
                "marketplace": Marketplace.redbubble.value,
                "design_path": str(design),
                "metadata": {},
            },
        )
        assert second.status_code == 429
