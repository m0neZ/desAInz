"""Integration tests for application shutdown behavior."""

import asyncio
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
from fastapi.testclient import TestClient

from backend.optimization.api import app, store
from backend.shared import http as http_module


def test_optimization_service_shutdown() -> None:
    """Start the service and ensure resources are cleaned up on shutdown."""
    with TestClient(app) as client:
        asyncio.run(http_module.get_async_http_client())
        resp = client.get("/health")
        assert resp.status_code == 200
    assert store._closed
    assert http_module._ASYNC_CLIENTS == {}
