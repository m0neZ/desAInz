"""Verify CORS headers for all FastAPI services."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

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
def test_cors_headers(base: str, module: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Allowed origins are returned in CORS preflight responses."""
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://example.com")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / base))
    mod = importlib.import_module(module)
    importlib.reload(mod)
    app = getattr(mod, "app")
    with TestClient(app) as client:
        resp = client.options(
            "/ready",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == "https://example.com"
