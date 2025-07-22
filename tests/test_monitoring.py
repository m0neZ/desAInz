"""Tests for the monitoring service."""

from pathlib import Path
import sys
from typing import Any

sys.path.append(
    str(Path(__file__).resolve().parents[1] / "backend" / "monitoring" / "src")
)  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

import importlib


def _get_client(monkeypatch: Any, **env: str) -> TestClient:
    """Return a ``TestClient`` for the monitoring app."""
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    import monitoring.main as main

    importlib.reload(main)
    return TestClient(main.app)


def test_metrics_endpoint(monkeypatch: Any) -> None:
    """Metrics endpoint should return prometheus data."""
    client = _get_client(monkeypatch)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.headers["Cache-Control"].startswith("public")


def test_overview_endpoint(monkeypatch: Any) -> None:
    """Overview should include cpu and memory usage."""
    client = _get_client(monkeypatch)
    response = client.get("/overview")
    assert response.status_code == 200
    body = response.json()
    assert "cpu_percent" in body
    assert "memory_mb" in body


def test_health_ready_endpoints(monkeypatch: Any) -> None:
    """Health and readiness should return status."""
    client = _get_client(monkeypatch)
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
    client = _get_client(monkeypatch)
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
    client = _get_client(monkeypatch, DAILY_SUMMARY_FILE=str(file_path))
    response = client.get("/daily_summary/report")
    assert response.status_code == 200
    assert response.json() == report
