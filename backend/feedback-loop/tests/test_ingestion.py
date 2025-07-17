"""Tests for performance metrics ingestion."""

from __future__ import annotations

import os
import importlib
from pathlib import Path
import sys

import pytest
from apscheduler.schedulers.background import BackgroundScheduler

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))


@pytest.fixture()
def _db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path}/ingest.db"
    import backend.shared.db as db

    importlib.reload(db)
    from backend.shared.db import Base, models as db_models  # noqa: F401

    Base.metadata.create_all(db.engine)
    try:
        yield db
    finally:
        Base.metadata.drop_all(db.engine)


def test_schedule_marketplace_ingestion(_db, requests_mock):
    """Job should store fetched metrics."""
    from feedback_loop import ingestion

    url = "http://api.example.com"
    requests_mock.get(
        f"{url}/listings/1/metrics",
        json={"views": 5, "favorites": 2, "orders": 1, "revenue": 3.5},
    )

    scheduler = BackgroundScheduler()
    job = ingestion.schedule_marketplace_ingestion(scheduler, url, [1], 1)
    job.func()

    with _db.session_scope() as session:
        row = session.query(ingestion.models.MarketplacePerformanceMetric).first()
        assert row is not None
        assert row.views == 5
        assert row.favorites == 2
        assert row.orders == 1
        assert row.revenue == 3.5
