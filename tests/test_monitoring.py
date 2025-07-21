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
    assert response.headers["Cache-Control"].startswith("public")


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
    assert response.headers["Cache-Control"].startswith("public")
    assert response.json() == {"status": "ok"}
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.headers["Cache-Control"].startswith("public")
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


def test_daily_summary_report_endpoint(tmp_path: Path, monkeypatch: Any) -> None:
    """Daily summary report endpoint returns persisted JSON."""
    import json

    report = {"ideas_generated": 1, "mockup_success_rate": 1.0, "marketplace_stats": {}}
    file_path = tmp_path / "report.json"
    file_path.write_text(json.dumps(report), encoding="utf-8")
    from monitoring import settings as monitoring_settings

    monkeypatch.setattr(
        monitoring_settings.settings, "daily_summary_file", str(file_path)
    )
    response = client.get("/daily_summary/report")
    assert response.status_code == 200
    assert response.json() == report
