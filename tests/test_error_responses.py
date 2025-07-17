"""Verify standardized error responses across services."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "backend" / "scoring-engine"))  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402
from backend.analytics import api as analytics_api  # noqa: E402
from backend.optimization import api as optimization_api  # noqa: E402
from backend.monitoring.src.monitoring import main as monitoring_main  # noqa: E402
from backend.marketplace_publisher.src import (  # noqa: E402
    marketplace_publisher as mp_main,
)  # noqa: E402
from backend.signal_ingestion import main as ingestion_main  # noqa: E402
from backend.api_gateway.src.api_gateway import main as gateway_main  # noqa: E402
from backend.service_template import main as template_main  # noqa: E402

from scoring_engine import app as scoring_app  # noqa: E402


def _assert_error(body: dict) -> None:
    assert "error" in body
    assert "correlation_id" in body
    assert "trace_id" in body


def test_fastapi_error_responses() -> None:
    """All FastAPI apps return standardized errors."""
    apps = [
        analytics_api.app,
        optimization_api.app,
        monitoring_main.app,
        mp_main.app,
        ingestion_main.app,
        gateway_main.app,
        template_main.app,
    ]
    for app in apps:
        client = TestClient(app)
        resp = client.get("/non-existent")
        assert resp.status_code == 404
        _assert_error(resp.json())


def test_scoring_error_response() -> None:
    """The scoring engine returns standardized errors."""
    client = TestClient(scoring_app.app)
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404
    _assert_error(resp.json())
