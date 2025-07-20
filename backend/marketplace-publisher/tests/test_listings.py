"""Tests for listing API endpoints."""

from __future__ import annotations

import importlib
from pathlib import Path

from fastapi.testclient import TestClient

import pytest


@pytest.fixture()
def _setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Create app and a listings table for tests."""

    async_url = f"sqlite+aiosqlite:///{tmp_path}/listings.db"
    sync_url = f"sqlite:///{tmp_path}/listings.db"
    monkeypatch.setenv("DATABASE_URL", async_url)
    from marketplace_publisher.main import app

    import backend.shared.db as db

    monkeypatch.setenv("DATABASE_URL", sync_url)
    importlib.reload(db)
    from backend.shared.db import Base, models

    Base.metadata.create_all(db.engine)
    with db.session_scope() as session:
        session.add(models.Listing(mockup_id=1, price=9.0, state="pending"))
    yield app
    Base.metadata.drop_all(db.engine)


def test_get_listing(_setup) -> None:
    """Fetch an existing listing."""

    app = _setup
    with TestClient(app) as client:
        resp = client.get("/listings/1")
        assert resp.status_code == 200
        assert resp.json()["state"] == "pending"


def test_patch_listing(_setup) -> None:
    """Update a listing's state."""

    app = _setup
    with TestClient(app) as client:
        resp = client.patch("/listings/1", json={"state": "active"})
        assert resp.status_code == 200
    import backend.shared.db as db
    from backend.shared.db import models

    with db.session_scope() as session:
        listing = session.get(models.Listing, 1)
        assert listing.state == "active"
