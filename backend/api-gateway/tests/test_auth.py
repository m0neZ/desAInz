# flake8: noqa
"""Tests for JWT auth middleware."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402
from typing import cast

from api_gateway.main import app  # noqa: E402
from backend.shared.db import Base, engine, session_scope  # noqa: E402
from backend.shared.db.models import UserRole  # noqa: E402

client = TestClient(app)


def get_token(username: str) -> str:
    """Return access token for ``username`` via the login endpoint."""
    resp = client.post("/auth/token", json={"username": username})
    assert resp.status_code == 200
    body = cast(dict[str, str], resp.json())
    return body["access_token"]


def setup_module(module: object) -> None:
    """Create tables for tests."""
    Base.metadata.create_all(engine)
    with session_scope() as session:
        session.add(UserRole(username="admin", role="admin"))


def teardown_module(module: object) -> None:
    """Drop tables after tests."""
    Base.metadata.drop_all(engine)


def test_login_issues_token() -> None:
    """Login endpoint returns a token for known users."""
    with session_scope() as session:
        session.add(UserRole(username="tester", role="viewer"))
    resp = client.post("/auth/token", json={"username": "tester"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_rejects_unknown_user() -> None:
    """Unknown users receive ``403``."""
    resp = client.post("/auth/token", json={"username": "ghost"})
    assert resp.status_code == 403


def test_protected_requires_token() -> None:
    """Ensure protected route rejects missing token."""
    response = client.get("/protected")
    assert response.status_code == 403


def test_protected_accepts_valid_token() -> None:
    """Ensure protected route accepts valid admin token."""
    token = get_token("admin")
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["user"] == "admin"


def test_protected_rejects_insufficient_role() -> None:
    """Ensure protected route rejects users without admin role."""
    with session_scope() as session:
        session.add(UserRole(username="viewer", role="viewer"))
    token = get_token("viewer")
    resp = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
