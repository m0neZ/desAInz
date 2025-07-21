"""Tests for default HTTP timeout handling in the API gateway."""

import importlib
from typing import Any

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from backend.shared.http import DEFAULT_TIMEOUT
import api_gateway.main as main_module
import api_gateway.routes as routes


class AssertTimeoutClient(httpx.AsyncClient):
    """``AsyncClient`` subclass asserting the provided timeout."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        assert kwargs.get("timeout") == DEFAULT_TIMEOUT
        super().__init__(*args, **kwargs)


@respx.mock
def test_system_health_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """``system_health`` should instantiate the client with the default timeout."""
    monkeypatch.setitem(routes, "HEALTH_ENDPOINTS", {"svc": "http://svc/health"})
    respx.get("http://svc/health").respond(200, json={"status": "ok"})
    monkeypatch.setattr(httpx, "AsyncClient", AssertTimeoutClient)
    importlib.reload(routes)
    client = TestClient(main_module.app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"svc": "ok"}
