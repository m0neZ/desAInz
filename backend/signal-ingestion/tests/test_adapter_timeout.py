"""Tests for timeout usage in the signal ingestion adapters."""

from types import TracebackType
from typing import Any, Optional

import httpx
import pytest
import respx
from signal_ingestion.adapters.base import BaseAdapter

from backend.shared.http import DEFAULT_TIMEOUT


class _DummyAdapter(BaseAdapter):
    """Minimal adapter for testing."""

    async def fetch(self) -> list[dict[str, object]]:
        return []


class AssertTimeoutClient:
    """Context manager mimicking ``AsyncClient`` and asserting timeout."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        assert kwargs.get("timeout") == DEFAULT_TIMEOUT

    async def __aenter__(self) -> "AssertTimeoutClient":
        """Enter context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        """Exit context manager without swallowing exceptions."""
        return None

    async def get(
        self, url: str, headers: dict[str, str] | None = None
    ) -> httpx.Response:
        request = httpx.Request("GET", url)
        return httpx.Response(200, json={}, request=request)


@respx.mock
@pytest.mark.asyncio()  # type: ignore[misc]
async def test_request_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify ``_request`` uses the default timeout."""
    monkeypatch.setattr(httpx, "AsyncClient", AssertTimeoutClient)
    adapter = _DummyAdapter(base_url="https://example.com", rate_limit=1)
    await adapter._request("/ping")
