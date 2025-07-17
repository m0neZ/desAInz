"""Tests for routing logic."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402
import httpx  # noqa: E402

from api_gateway.main import app  # noqa: E402
from api_gateway.auth import create_access_token  # noqa: E402
from types import TracebackType  # noqa: E402
from typing import Any, Optional, Type  # noqa: E402

client = TestClient(app)


def test_status() -> None:
    """Status endpoint should return OK."""
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


import pytest  # noqa: E402


def test_trpc_ping(monkeypatch: pytest.MonkeyPatch) -> None:
    """Proxy tRPC ping to backend service."""
    token = create_access_token({"sub": "tester"})

    class MockClient:
        async def __aenter__(self) -> "MockClient":
            return self

        async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc: Optional[BaseException],
            tb: Optional[TracebackType],
        ) -> None:
            return None

        async def post(
            self,
            url: str,
            json: Any | None = None,
            headers: dict[str, str] | None = None,
        ) -> httpx.Response:
            assert url.endswith("/trpc/ping")
            assert headers == {"Authorization": f"Bearer {token}"}
            return httpx.Response(
                200,
                json={"result": {"message": "pong", "user": "tester"}},
            )

    monkeypatch.setattr("api_gateway.routes.TRPC_SERVICE_URL", "http://backend:8000")
    monkeypatch.setattr(httpx, "AsyncClient", MockClient)
    response = client.post(
        "/trpc/ping",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["result"]["message"] == "pong"
    assert body["result"]["user"] == "tester"
