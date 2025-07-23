"""API endpoint tests for the monitoring service."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import sys

import importlib
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
import os
import prometheus_client
from prometheus_client import CollectorRegistry

os.environ.setdefault("METRICS_DB_URL", "sqlite:///:memory:")
prometheus_client.REGISTRY = CollectorRegistry()
import monitoring.main as main_module


def _get_client(monkeypatch: Any, **env: str) -> TestClient:
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    importlib.reload(main_module)
    return TestClient(main_module.app)


def test_basic_endpoints(monkeypatch: Any, tmp_path: Path) -> None:
    """Ensure latency and queue endpoints respond."""
    log_file = tmp_path / "app.log"
    log_file.write_text("", encoding="utf-8")
    client = _get_client(
        monkeypatch,
        DAILY_SUMMARY_FILE=str(tmp_path / "summary.json"),
        LOG_FILE=str(log_file),
        METRICS_DB_URL="sqlite:///:memory:",
    )

    resp = client.get("/latency")
    assert resp.status_code == 200

    resp = client.get("/queue_length")
    assert resp.status_code == 200
