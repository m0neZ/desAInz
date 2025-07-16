"""Tests for the monitoring service."""

from fastapi.testclient import TestClient

from backend.monitoring.main import app

client = TestClient(app)


def test_overview() -> None:
    """Monitoring overview should return cpu and memory metrics."""
    response = client.get("/overview")
    assert response.status_code == 200
    body = response.json()
    assert "cpu_percent" in body
    assert "memory_mb" in body


def test_metrics_endpoint() -> None:
    """Prometheus metrics endpoint should expose text format."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
