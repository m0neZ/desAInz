"""Tests for scoring engine health endpoints."""

# mypy: ignore-errors

from fastapi.testclient import TestClient

from scoring_engine.app import app

client = TestClient(app)


def test_health_ready() -> None:
    """Health and readiness endpoints return status."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ready"}
