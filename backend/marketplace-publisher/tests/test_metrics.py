"""Tests for marketplace metrics endpoints."""  # noqa: E402

from __future__ import annotations

from pathlib import Path
from fastapi.testclient import TestClient
import importlib
import pytest


@pytest.fixture()
def _setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Create a temporary DB with sample metric."""
    async_url = f"sqlite+aiosqlite:///{tmp_path}/metrics.db"
    sync_url = f"sqlite:///{tmp_path}/metrics.db"
    monkeypatch.setenv("DATABASE_URL", async_url)
    from marketplace_publisher.main import app
    import backend.shared.db as db

    monkeypatch.setenv("DATABASE_URL", sync_url)
    importlib.reload(db)
    from backend.shared.db import Base, models

    Base.metadata.create_all(db.engine)
    with db.session_scope() as session:
        session.add(
            models.MarketplacePerformanceMetric(
                listing_id=1, views=1, favorites=2, orders=3, revenue=4.0
            )
        )
    yield app
    Base.metadata.drop_all(db.engine)


def test_metrics_route(_setup) -> None:
    """GET /metrics should return stored data."""
    app = _setup
    with TestClient(app) as client:
        resp = client.get("/metrics/1")
        assert resp.status_code == 200
        assert resp.json()["orders"] == 3
