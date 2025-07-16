"""Tests for the monitoring service."""

from __future__ import annotations

from backend.monitoring.app import app


def test_overview_endpoint() -> None:
    """Verify the overview endpoint returns the expected data."""
    client = app.test_client()
    response = client.get("/overview")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_metrics_endpoint() -> None:
    """Ensure metrics endpoint is reachable."""
    client = app.test_client()
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"monitoring_request_count" in response.data
