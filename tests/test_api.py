"""Tests for the optimization API."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from backend.optimization.api import app


client = TestClient(app)


def test_add_metric_and_get_optimizations() -> None:
    """Ensure metrics endpoint stores data and returns suggestions."""
    metric = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu_percent": 90,
        "memory_mb": 2048,
    }
    response = client.post("/metrics", json=metric)
    assert response.status_code == 200
    response = client.get("/optimizations")
    assert response.status_code == 200
    assert response.json() != []
