"""Verify standardized error responses across services."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient
from backend.analytics import api as analytics_api
from backend.optimization import api as optimization_api
from backend.monitoring.src.monitoring import main as monitoring_main
from backend.marketplace_publisher.src import marketplace_publisher as mp_main
from backend.signal_ingestion import main as ingestion_main
from backend.api_gateway.src.api_gateway import main as gateway_main
from backend.service_template import main as template_main
from flask.testing import FlaskClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "backend" / "scoring-engine"))
from scoring_engine import app as scoring_app


def _assert_error(body: dict) -> None:
    assert "error" in body
    assert "correlation_id" in body
    assert "trace_id" in body


def test_fastapi_error_responses() -> None:
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


def test_flask_error_response() -> None:
    client: FlaskClient = scoring_app.app.test_client()
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404
    _assert_error(resp.get_json())
