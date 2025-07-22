"""Verify /metrics endpoint across FastAPI services."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from prometheus_client.parser import text_string_to_metric_families

SERVICES = [
    ("backend/service-template/src", "main"),
    ("backend/api-gateway/src", "api_gateway.main"),
    ("backend/signal-ingestion/src", "signal_ingestion.main"),
    ("backend/feedback-loop/feedback_loop", "feedback_loop.main"),
    ("backend/marketplace-publisher/src", "marketplace_publisher.main"),
    ("backend/mockup-generation/mockup_generation", "mockup_generation.api"),
    ("backend/analytics", "backend.analytics.api"),
    ("backend/optimization", "backend.optimization.api"),
    ("backend/scoring-engine/scoring_engine", "scoring_engine.app"),
    ("backend/monitoring/src", "monitoring.main"),
]


@pytest.mark.parametrize("base,module", SERVICES)
def test_metrics_endpoint(base: str, module: str) -> None:
    """All services should expose Prometheus metrics."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / base))
    mod = importlib.import_module(module)
    importlib.reload(mod)
    app = getattr(mod, "app")
    with TestClient(app) as client:
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/plain")
        assert b"# TYPE" in resp.content
        metrics = {m.name for m in text_string_to_metric_families(resp.text)}
        assert "http_requests_total" in metrics
