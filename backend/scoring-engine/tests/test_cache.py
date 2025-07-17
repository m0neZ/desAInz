"""Tests for Redis caching behavior."""

from datetime import datetime, timezone

import fakeredis.aioredis
from fastapi.testclient import TestClient

import scoring_engine.app as scoring_module
from scoring_engine import app
from scoring_engine.weight_repository import update_weights


def setup_module(module) -> None:
    """Use fakeredis for tests."""
    scoring_module.redis_client = fakeredis.aioredis.FakeRedis()


def test_score_endpoint_caches() -> None:
    """Ensure score endpoint caches results in Redis."""
    client = TestClient(app.app)
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
        "metadata": {"a": 1.0},
        "centroid": [0.0, 1.0],
        "median_engagement": 1.0,
        "topics": ["t"],
    }
    resp1 = client.post("/score", json=payload)
    assert resp1.json["cached"] is False
    resp2 = client.post("/score", json=payload)
    assert resp2.json["cached"] is True
