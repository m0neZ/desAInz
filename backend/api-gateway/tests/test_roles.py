"""Tests for role-based access control."""

from __future__ import annotations

import os
from pathlib import Path
import sys

# Configure in-memory database before importing the app
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

from backend.shared.db import engine, session_scope  # noqa: E402
from backend.shared.db.base import Base  # noqa: E402
from backend.shared.db.models import Role  # noqa: E402
from api_gateway.main import app  # noqa: E402
from api_gateway.auth import create_access_token  # noqa: E402

Base.metadata.create_all(engine)
with session_scope() as session:
    session.add_all(
        [Role(id=1, name="admin"), Role(id=2, name="editor"), Role(id=3, name="viewer")]
    )

client = TestClient(app)


def test_protected_allows_viewer() -> None:
    """Protected route should allow viewer role."""
    token = create_access_token({"sub": "user1", "role": "viewer"})
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_protected_rejects_editor() -> None:
    """Protected route should reject role without viewer permission."""
    token = create_access_token({"sub": "user1", "role": "editor"})
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_assign_role() -> None:
    """Admin can assign role to a user."""
    admin_token = create_access_token({"sub": "admin", "role": "admin"})
    resp = client.post(
        "/roles/user2",
        params={"role": "editor"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "assigned"}
