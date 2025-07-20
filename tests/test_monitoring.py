"""Tests for the monitoring service."""

from pathlib import Path
import sys
from typing import Any

sys.path.append(
    str(Path(__file__).resolve().parents[1] / "backend" / "monitoring" / "src")
)  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

from monitoring.main import app  # noqa: E402

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


def test_health_ready_endpoints() -> None:
    """Health and readiness should return status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_daily_summary_endpoint(monkeypatch: Any) -> None:
    """Daily summary endpoint returns generated summary."""
    from unittest.mock import AsyncMock

    monkeypatch.setattr(
        "monitoring.main.generate_daily_summary",
        AsyncMock(
            return_value={
                "ideas_generated": 1,
                "mockup_success_rate": 1.0,
                "marketplace_stats": {},
            }
        ),
    )
    response = client.get("/daily_summary")
    assert response.status_code == 200
    body = response.json()
    assert body["ideas_generated"] == 1
