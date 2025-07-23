"""Tests for the optimization API."""

from pathlib import Path
import sys

sys.path.append(
    str(Path(__file__).resolve().parents[1] / "backend" / "optimization")
)  # noqa: E402

from datetime import UTC, datetime  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

from backend.optimization.api import app  # noqa: E402


client = TestClient(app)


def test_add_metric_and_get_optimizations() -> None:
    """Ensure metrics endpoint stores data and returns suggestions."""
    metric = {
        "timestamp": datetime.now(UTC).isoformat(),
        "cpu_percent": 90,
        "memory_mb": 2048,
    }
    response = client.post("/metrics", json=metric)
    assert response.status_code == 200
    response = client.get("/optimizations")
    assert response.status_code == 200
    assert response.json() != []
    response = client.get("/recommendations")
    assert response.status_code == 200
    assert response.json() != []


def test_health_ready_endpoints() -> None:
    """Health and readiness endpoints return status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers["Cache-Control"].startswith("public")
    assert response.json() == {"status": "ok"}
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.headers["Cache-Control"].startswith("public")
    assert response.json() == {"status": "ready"}
