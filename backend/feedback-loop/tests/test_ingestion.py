"""Tests for performance metrics ingestion."""

from __future__ import annotations

import os
import importlib
from pathlib import Path
import sys

import pytest
from apscheduler.schedulers.background import BackgroundScheduler
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
sys.path.append(str(ROOT.parent / "scoring-engine"))


@pytest.fixture()
def _db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path}/ingest.db"
    monkeypatch.setitem(
        sys.modules,
        "backend.shared.tracing",
        types.SimpleNamespace(configure_tracing=lambda *a, **k: None),
    )
    import warnings

    warnings.filterwarnings("ignore", category=DeprecationWarning)
    monkeypatch.setitem(
        sys.modules,
        "scoring_engine",
        types.SimpleNamespace(
            weight_repository=types.SimpleNamespace(update_weights=lambda **k: None)
        ),
    )
    import backend.shared.db as db

    importlib.reload(db)
    from backend.shared.db import Base, models as db_models  # noqa: F401

    Base.metadata.create_all(db.engine)
    try:
        yield db
    finally:
        Base.metadata.drop_all(db.engine)


def test_schedule_marketplace_ingestion(_db) -> None:
    """Job should store fetched metrics."""
    import importlib.util

    pkg = types.ModuleType("feedback_loop")
    sys.modules["feedback_loop"] = pkg
    spec_wu = importlib.util.spec_from_file_location(
        "feedback_loop.weight_updater", ROOT / "feedback_loop" / "weight_updater.py"
    )
    weight_updater = importlib.util.module_from_spec(spec_wu)
    assert spec_wu.loader
    spec_wu.loader.exec_module(weight_updater)
    sys.modules["feedback_loop.weight_updater"] = weight_updater
    pkg.weight_updater = weight_updater
    spec = importlib.util.spec_from_file_location(
        "feedback_loop.ingestion", ROOT / "feedback_loop" / "ingestion.py"
    )
    ingestion = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(ingestion)
    sys.modules["feedback_loop.ingestion"] = ingestion

    class DummyClient:
        base_url = "http://api.example.com"

        def get_listing_metrics(self, listing_id: int) -> dict[str, float]:
            assert listing_id == 1
            return {"views": 5, "favorites": 2, "orders": 1, "revenue": 3.5}

    scheduler = BackgroundScheduler()
    ingestion.CLIENTS = {"dummy": DummyClient()}  # type: ignore[attr-defined]
    called = False

    def _fake_update(url: str) -> dict[str, float]:
        nonlocal called
        called = True
        return {}

    ingestion.update_weights_from_db = _fake_update  # type: ignore[assignment]
    job = ingestion.schedule_marketplace_ingestion(
        scheduler, [1], "http://api.example.com", 1
    )
    job.func()
    assert called

    with _db.session_scope() as session:
        row = session.query(ingestion.models.MarketplacePerformanceMetric).first()
        assert row is not None
        assert row.views == 5
        assert row.favorites == 2
        assert row.orders == 1
        assert row.revenue == 3.5


def test_update_weights_from_db(_db, requests_mock):
    """Aggregated metrics should update stored weights."""
    import importlib.util

    pkg = types.ModuleType("feedback_loop")
    sys.modules["feedback_loop"] = pkg
    spec_wu = importlib.util.spec_from_file_location(
        "feedback_loop.weight_updater", ROOT / "feedback_loop" / "weight_updater.py"
    )
    weight_updater = importlib.util.module_from_spec(spec_wu)
    assert spec_wu.loader
    spec_wu.loader.exec_module(weight_updater)
    sys.modules["feedback_loop.weight_updater"] = weight_updater
    pkg.weight_updater = weight_updater
    spec = importlib.util.spec_from_file_location(
        "feedback_loop.ingestion", ROOT / "feedback_loop" / "ingestion.py"
    )
    ingestion = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(ingestion)
    sys.modules["feedback_loop.ingestion"] = ingestion

    url = "http://api.example.com"
    requests_mock.post(f"{url}/weights/feedback", json={})

    with _db.session_scope() as session:
        session.add_all(
            [
                ingestion.models.MarketplacePerformanceMetric(
                    listing_id=1,
                    views=10,
                    favorites=4,
                    orders=2,
                    revenue=5.0,
                ),
                ingestion.models.MarketplacePerformanceMetric(
                    listing_id=2,
                    views=5,
                    favorites=1,
                    orders=1,
                    revenue=2.0,
                ),
            ]
        )

    weights = ingestion.update_weights_from_db(url)
    assert requests_mock.called
    assert round(weights["engagement"], 2) == 0.33
    assert round(weights["community_fit"], 2) == 0.6
