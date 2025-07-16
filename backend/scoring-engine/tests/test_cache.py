"""Tests for Redis caching behavior."""

from datetime import datetime, timezone

import fakeredis
from flask.testing import FlaskClient

from scoring_engine.app import app, redis_client
from scoring_engine.weight_repository import update_weights


app.config.update(TESTING=True)


def setup_module(module):
    """Use fakeredis for tests."""
    redis_client.connection_pool.connection_class = fakeredis.FakeConnection


def test_score_endpoint_caches():
    """Ensure score endpoint caches results in Redis."""
    client: FlaskClient = app.test_client()
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
