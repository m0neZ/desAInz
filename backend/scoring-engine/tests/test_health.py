"""Tests for scoring engine health endpoints."""

from flask.testing import FlaskClient

from scoring_engine.app import app

app.config.update(TESTING=True)
client: FlaskClient = app.test_client()


def test_health_ready() -> None:
    """Health and readiness endpoints return status."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ready"}
