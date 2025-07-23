"""API endpoint tests for the optimization service."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from pathlib import Path

from backend.optimization import api as opt_api
from backend.optimization.storage import MetricsStore


def test_recommendation_routes(tmp_path: Path) -> None:
    """Ensure optimization endpoints return recommendations."""
    opt_api.store = MetricsStore(f"sqlite:///{tmp_path/'metrics.db'}")
    client = TestClient(opt_api.app)

    metric = {
        "timestamp": datetime.now(UTC).isoformat(),
        "cpu_percent": 85.0,
        "memory_mb": 2048.0,
        "disk_usage_mb": 4096.0,
    }
    resp = client.post("/metrics", json=metric)
    assert resp.status_code == 200

    resp = client.get("/optimizations")
    assert resp.status_code == 200
    assert resp.json() != []

    resp = client.get("/recommendations")
    assert resp.status_code == 200
    assert resp.json() != []

    resp = client.get("/cost_alerts")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

    resp = client.get("/hints")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
