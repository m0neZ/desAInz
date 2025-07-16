"""Tests for the monitoring service."""

from fastapi.testclient import TestClient

from monitoring.main import app
from backend.shared.db import engine
from backend.shared.db.base import Base

Base.metadata.create_all(engine)

client = TestClient(app)


def test_metrics_endpoint() -> None:
    """Metrics endpoint should return prometheus data."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")


def test_overview_endpoint() -> None:
    """Overview should include cpu and memory usage."""
    response = client.get("/overview")
    assert response.status_code == 200
    body = response.json()
    assert "cpu_percent" in body
    assert "memory_mb" in body


def test_analytics_endpoints() -> None:
    """Analytics endpoints should return JSON data."""
    resp_ab = client.get("/analytics/ab-tests")
    assert resp_ab.status_code == 200
    assert isinstance(resp_ab.json(), list)
    resp_market = client.get("/analytics/marketplace")
    assert resp_market.status_code == 200
    assert isinstance(resp_market.json(), list)
