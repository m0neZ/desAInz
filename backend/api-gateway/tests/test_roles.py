"""Tests for role management endpoints."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

from api_gateway.main import app  # noqa: E402
from api_gateway.auth import create_access_token  # noqa: E402
from backend.shared.db import Base, engine, session_scope  # noqa: E402
from backend.shared.db.models import UserRole  # noqa: E402

client = TestClient(app)


def setup_module(module: object) -> None:
    """Create tables for the in-memory database."""
    Base.metadata.create_all(engine)
    with session_scope() as session:
        session.add(UserRole(username="admin", role="admin"))


def teardown_module(module: object) -> None:
    """Drop tables after tests."""
    Base.metadata.drop_all(engine)


def test_assign_and_list_roles() -> None:
    """Assign a role and verify it is listed."""
    token = create_access_token({"sub": "admin"})
    resp = client.post(
        "/roles/user1",
        json={"role": "editor"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    resp = client.get("/roles?limit=50&page=0", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert {"username": "user1", "role": "editor"} in resp.json()
