"""Tests for tracing and profiling middleware across services."""

import importlib
import logging
import os
import sys
from pathlib import Path

import pytest
from opentelemetry import trace
from fastapi.testclient import TestClient

SERVICES = [
    (
        "backend/api-gateway/src",
        "api_gateway.main",
        "fastapi",
    ),
    (
        "backend/analytics",
        "backend.analytics.api",
        "fastapi",
    ),
    (
        "backend/optimization",
        "backend.optimization.api",
        "fastapi",
    ),
    (
        "backend/service-template/src",
        "main",
        "fastapi",
    ),
    (
        "backend/signal-ingestion/src",
        "signal_ingestion.main",
        "fastapi",
    ),
    (
        "backend/monitoring/src",
        "monitoring.main",
        "fastapi",
    ),
    (
        "backend/marketplace-publisher/src",
        "marketplace_publisher.main",
        "fastapi",
    ),
    (
        "backend/scoring-engine/scoring_engine",
        "scoring_engine.app",
        "fastapi",
    ),
]


@pytest.mark.parametrize("base,module,framework", SERVICES)
def test_tracing_and_profiling(
    base: str, module: str, framework: str, caplog: pytest.LogCaptureFixture
) -> None:
    """Ensure tracing and profiling middleware are configured."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / base))
    os.environ["SERVICE_NAME"] = "test-service"
    mod = importlib.import_module(module)
    importlib.reload(mod)
    app = getattr(mod, "app")

    caplog.set_level(logging.INFO)
    if framework == "fastapi":
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.headers["Cache-Control"].startswith("public")
    else:
        app.config.update(TESTING=True)
        client = app.test_client()
        resp = client.get("/health")
        assert resp.status_code == 200

    assert any("request timing" in record.getMessage() for record in caplog.records)
    provider = trace.get_tracer_provider()
    assert provider.resource.attributes.get("service.name") == "test-service"
