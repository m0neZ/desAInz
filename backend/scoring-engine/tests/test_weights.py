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


def test_feedback_weight_smoothing() -> None:
    """Repeated feedback should adjust weights gradually."""
    client = TestClient(app)
    reset_payload = {
        "freshness": 1.0,
        "engagement": 1.0,
        "novelty": 1.0,
        "community_fit": 1.0,
        "seasonality": 1.0,
    }
    client.put("/weights", json=reset_payload)

    payload = {
        "freshness": 0.0,
        "engagement": 0.0,
        "novelty": 0.0,
        "community_fit": 0.0,
        "seasonality": 0.0,
    }
    smoothing = scoring_module.weight_repository.FEEDBACK_SMOOTHING
    iterations = 5
    for _ in range(iterations):
        resp = client.post("/weights/feedback", json=payload)
        assert resp.status_code == 200

    resp = client.get("/weights")
    data = resp.json()
    expected = (1 - smoothing) ** iterations
    for key in payload:
        assert round(data[key], 5) == round(expected, 5)
