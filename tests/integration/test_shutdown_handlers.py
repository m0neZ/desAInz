"""Verify service shutdown releases resources."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

SERVICES = [
    ("backend/service-template/src", "main", None),
    ("backend/api-gateway/src", "api_gateway.main", None),
    ("backend/signal-ingestion/src", "signal_ingestion.main", None),
    ("backend/feedback-loop/feedback_loop", "feedback_loop.main", None),
    ("backend/marketplace-publisher/src", "marketplace_publisher.main", None),
    ("backend/optimization", "backend.optimization.api", "store"),
    ("backend/scoring-engine/scoring_engine", "scoring_engine.app", None),
    ("backend/monitoring/src", "monitoring.main", "metrics_store"),
]


@pytest.mark.parametrize("base,module,store_attr", SERVICES)
def test_shutdown_releases_resources(
    base: str, module: str, store_attr: str | None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Start ``module`` application and verify shutdown handlers."""
    monkeypatch.setenv("ALLOW_STATUS_UNAUTHENTICATED", "true")
    monkeypatch.setenv("SKIP_MIGRATIONS", "1")
    monkeypatch.setenv("SCORING_ENGINE_KAFKA_SKIP", "1")

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / base))
    mod = importlib.import_module(module)
    importlib.reload(mod)

    called = {"clients": 0, "store": 0}

    async def fake_close_clients() -> None:
        called["clients"] += 1

    monkeypatch.setattr(mod, "close_async_clients", fake_close_clients, raising=False)

    if store_attr:
        store = getattr(mod, store_attr)

        def fake_close() -> None:
            called["store"] += 1

        monkeypatch.setattr(store, "close", fake_close)

    if hasattr(mod, "start_rate_updater"):
        monkeypatch.setattr(mod, "start_rate_updater", lambda: None)
    if hasattr(mod, "load_default_rules"):
        monkeypatch.setattr(mod, "load_default_rules", lambda watch=False: None)
    if hasattr(mod, "start_centroid_scheduler"):
        monkeypatch.setattr(mod, "start_centroid_scheduler", lambda: None)
    if hasattr(mod, "_create_consumer"):
        monkeypatch.setattr(
            mod, "_create_consumer", lambda: SimpleNamespace(close=lambda: None)
        )

    app = getattr(mod, "app")
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
    assert called["clients"] == 1
    if store_attr:
        assert called["store"] == 1
