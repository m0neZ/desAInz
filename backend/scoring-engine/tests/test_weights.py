"""Tests for weight update endpoint."""

# mypy: ignore-errors

from fastapi.testclient import TestClient
import importlib
from scoring_engine.app import app

scoring_module = importlib.import_module("scoring_engine.app")


def setup_module(module) -> None:
    """Use fakeredis for tests."""
    from tests import DummyRedis

    scoring_module.redis_client = DummyRedis()


def test_feedback_weight_update() -> None:
    """Weights updated via feedback endpoint persist."""
    client = TestClient(app)
    payload = {
        "freshness": 0.5,
        "engagement": 0.4,
        "novelty": 0.3,
        "community_fit": 0.2,
        "seasonality": 0.1,
    }
    resp = client.post("/weights/feedback", json=payload)
    assert resp.status_code == 200
    resp = client.get("/weights")
    data = resp.json()
    for key, val in payload.items():
        assert data[key] == val
