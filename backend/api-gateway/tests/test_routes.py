"""Tests for routing logic."""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

from api_gateway.main import app  # noqa: E402
from api_gateway.auth import create_access_token  # noqa: E402

client = TestClient(app)


def test_status() -> None:
    """Status endpoint should return OK."""
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_trpc_ping() -> None:
    """TRPC ping should return pong."""
    token = create_access_token({"sub": "tester", "role": "viewer"})
    response = client.post(
        "/trpc/ping",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["result"]["message"] == "pong"
    assert body["result"]["user"] == "tester"
