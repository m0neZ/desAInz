"""Tests for the monitoring service."""

from fastapi.testclient import TestClient

from backend.monitoring.main import app

client = TestClient(app)


def test_metrics_endpoint() -> None:
    """Ensure the metrics endpoint returns Prometheus data."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "python_info" in response.text


def test_overview_endpoint() -> None:
    """Verify the overview endpoint returns system status."""
    response = client.get("/overview")
    assert response.status_code == 200
    assert response.json()["status"] == "operational"


def test_logs_endpoint() -> None:
    """Check logs endpoint returns text even if log file missing."""
    response = client.get("/logs")
    assert response.status_code == 200
    assert "logs" in response.json()
