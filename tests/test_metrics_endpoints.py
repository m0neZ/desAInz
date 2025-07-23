"""Verify /metrics endpoint across FastAPI services."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
import warnings

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


def _gateway_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Return an ``api-gateway`` test client with mocked dependencies."""
    monkeypatch.setenv("OPTIMIZATION_URL", "http://opt:5007")
    monkeypatch.setenv("MONITORING_URL", "http://mon:8000")
    monkeypatch.setenv("API_GATEWAY_REQUEST_CACHE_TTL", "1")
    monkeypatch.setenv("SDK_DISABLED", "1")
    sys.path.insert(
        0, str(Path(__file__).resolve().parents[1] / "backend" / "api-gateway" / "src")
    )
    import api_gateway.routes as routes
    import api_gateway.main as main
    import prometheus_client
    from prometheus_client import CollectorRegistry
    import httpx

    class MockClient:
        async def __aenter__(self) -> "MockClient":
            return self

        async def __aexit__(
            self,
            exc_type: object,
            exc: object,
            tb: object,
        ) -> None:
            return None

        async def get(self, url: str) -> httpx.Response:
            if url == "http://opt:5007/metrics":
                return httpx.Response(200, content=b"opt")
            if url == "http://mon:8000/metrics":
                return httpx.Response(200, content=b"mon")
            return httpx.Response(404)

    monkeypatch.setattr(httpx, "AsyncClient", MockClient)
    prometheus_client.REGISTRY = CollectorRegistry()
    importlib.reload(routes)
    return TestClient(main.app)


def test_proxy_optimization_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    """API gateway should proxy optimization metrics."""
    client = _gateway_client(monkeypatch)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    resp = client.get("/optimization/metrics")
    assert resp.status_code == 200
    assert resp.text == "opt"


def test_proxy_monitoring_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    """API gateway should proxy monitoring metrics."""
    client = _gateway_client(monkeypatch)
    resp = client.get("/monitoring/metrics")
    assert resp.status_code == 200
    assert resp.text == "mon"
