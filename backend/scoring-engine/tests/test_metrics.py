"""Tests for cache metrics endpoint."""

from datetime import datetime, timezone

import fakeredis.aioredis
from fastapi.testclient import TestClient

import scoring_engine.app as scoring_module
from scoring_engine.app import app
from scoring_engine.weight_repository import update_weights


def setup_module(module) -> None:
    """Use fakeredis for tests."""
    scoring_module.redis_client = fakeredis.aioredis.FakeRedis()


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
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engagement_rate": 1.0,
        "embedding": [1.0, 0.0],
    }
    # first request miss
    client.post("/score", json=payload)
    # second request hit
    client.post("/score", json=payload)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cache_hits"] == 1
    assert data["cache_misses"] == 1
