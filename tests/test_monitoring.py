"""Tests for the monitoring service."""

from fastapi.testclient import TestClient

from monitoring.main import app

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
