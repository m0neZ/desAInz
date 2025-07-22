"""Tests for cache metrics endpoint."""

# mypy: ignore-errors

import importlib
import warnings
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from scoring_engine.app import app
from scoring_engine.weight_repository import update_weights

scoring_module = importlib.import_module("scoring_engine.app")


def setup_module(module) -> None:
    """Use fakeredis for tests."""
    from tests import DummyRedis

    scoring_module.redis_client = DummyRedis()
    warnings.filterwarnings("ignore", category=ResourceWarning)


def _get_metric(payload: str, name: str) -> float:
    for line in payload.splitlines():
        if line.startswith(name):
            return float(line.split(" ")[1])
    raise AssertionError(f"metric {name} not found")


def test_metrics_endpoint_counts_hits_and_misses() -> None:
    """/metrics returns correct cache hit and miss counts."""
    client = TestClient(app)
    update_weights(
        freshness=1.0,
        engagement=1.0,
        novelty=1.0,
        community_fit=1.0,
        seasonality=1.0,
    )
    payload = {
        "timestamp": datetime.utcnow().replace(tzinfo=UTC).isoformat(),
        "engagement_rate": 1.0,
        "embedding": [1.0, 0.0],
    }
    # first request miss
    client.post("/score", json=payload)
    # second request hit
    client.post("/score", json=payload)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    metrics_text = resp.text
    assert _get_metric(metrics_text, "cache_hits_total") >= 1.0
    assert _get_metric(metrics_text, "cache_misses_total") >= 1.0
