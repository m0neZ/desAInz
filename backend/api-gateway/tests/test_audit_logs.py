"""Tests for audit log endpoint."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from api_gateway.auth import create_access_token  # noqa: E402
from api_gateway.main import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.shared.db import Base, engine, session_scope  # noqa: E402
from backend.shared.db.models import UserRole  # noqa: E402

client = TestClient(app)


def setup_module(module: object) -> None:
    """Create tables for tests."""
    Base.metadata.create_all(engine)
    with session_scope() as session:
        session.add(UserRole(username="admin", role="admin"))


def teardown_module(module: object) -> None:
    """Drop tables after tests."""
    Base.metadata.drop_all(engine)


def test_audit_log_creation_and_query() -> None:
    """Assign role and retrieve audit log entry."""
    token = create_access_token({"sub": "admin"})
    client.post(
        "/roles/user2",
        json={"role": "viewer"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = client.get("/audit-logs", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert any(item["action"] == "assign_role" for item in data["items"])
