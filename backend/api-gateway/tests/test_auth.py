"""Tests for JWT auth middleware."""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from api_gateway.main import app  # noqa: E402
from api_gateway.auth import create_access_token  # noqa: E402

client = TestClient(app)


def test_protected_requires_token() -> None:
    """Ensure protected route rejects missing token."""
    response = client.get("/protected")
    assert response.status_code == 403


def test_protected_accepts_valid_token() -> None:
    """Ensure protected route accepts valid token."""
    token = create_access_token({"sub": "user1"})
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["user"] == "user1"
