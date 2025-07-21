"""Integration tests for Timescale metrics storage when scoring."""

# mypy: ignore-errors

from datetime import datetime, timezone
from pathlib import Path
import importlib
import sqlite3

from fastapi.testclient import TestClient

from scoring_engine.app import app
from scoring_engine.weight_repository import update_weights

scoring_module = importlib.import_module("scoring_engine.app")


def setup_module(module) -> None:
    """Use fakeredis for tests."""
    from tests.test_search_api import DummyRedis

    scoring_module.redis_client = DummyRedis()


def _count_rows(db: Path) -> int:
    with sqlite3.connect(db) as conn:
        cur = conn.execute("SELECT COUNT(*) FROM scores")
        return int(cur.fetchone()[0])


def test_score_metrics_written_once(monkeypatch, tmp_path: Path) -> None:
    """Score endpoint should insert one metrics row for new scores only."""
    db_path = tmp_path / "metrics.db"
    store = scoring_module.TimescaleMetricsStore(f"sqlite:///{db_path}")
    monkeypatch.setattr(scoring_module, "metrics_store", store)

    client = TestClient(app)
    update_weights(
        freshness=1.0,
        engagement=1.0,
        novelty=1.0,
        community_fit=1.0,
        seasonality=1.0,
    )
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engagement_rate": 1.0,
        "embedding": [1.0, 0.0],
    }
    client.post("/score", json=payload)
    client.post("/score", json=payload)
    assert _count_rows(db_path) == 1
