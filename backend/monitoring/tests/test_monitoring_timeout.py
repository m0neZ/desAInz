"""Tests for timeout configuration in the monitoring service."""

from typing import Any

import httpx
import monitoring.main as main_module
import pytest
import respx

from backend.shared.http import DEFAULT_TIMEOUT


class AssertTimeoutClient(httpx.AsyncClient):
    """``AsyncClient`` subclass asserting the provided timeout."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        assert kwargs.get("timeout") == DEFAULT_TIMEOUT
        super().__init__(*args, **kwargs)


@respx.mock
@pytest.mark.asyncio()  # type: ignore[misc]
async def test_status_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """``status`` should use the default timeout for HTTP requests."""
    respx.get("http://mockup-generation:8000/health").respond(
        200, json={"status": "ok"}
    )
    respx.get("http://marketplace-publisher:8000/health").respond(
        200, json={"status": "ok"}
    )
    respx.get("http://orchestrator:8000/health").respond(200, json={"status": "ok"})
    monkeypatch.setattr(httpx, "AsyncClient", AssertTimeoutClient)
    result = await main_module.status()
    assert result == {
        "mockup_generation": "ok",
        "marketplace_publisher": "ok",
        "orchestrator": "ok",
    }
