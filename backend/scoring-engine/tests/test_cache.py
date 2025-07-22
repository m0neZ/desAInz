"""Tests for Redis caching behavior."""

# mypy: ignore-errors

import importlib
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from scoring_engine import app
from scoring_engine.weight_repository import update_weights

scoring_module = importlib.import_module("scoring_engine.app")


def setup_module(module) -> None:
    """Use fakeredis for tests."""
    from tests import DummyRedis

    scoring_module.redis_client = DummyRedis()


def test_score_endpoint_caches() -> None:
    """Ensure score endpoint caches results in Redis."""
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
        "metadata": {"a": 1.0},
        "source": "global",
        "median_engagement": 1.0,
        "topics": ["t"],
    }
    resp1 = client.post("/score", json=payload)
    assert resp1.json()["cached"] is False
    resp2 = client.post("/score", json=payload)
    assert resp2.json()["cached"] is True
