"""Tests for API Gateway role handling."""

import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parents[1] / "backend" / "api-gateway" / "src")
)

from fastapi.testclient import TestClient  # noqa: E402
from api_gateway.main import app  # noqa: E402
from api_gateway.auth import create_access_token  # noqa: E402
from backend.shared.db import engine, session_scope  # noqa: E402
from backend.shared.db.base import Base  # noqa: E402
from backend.shared.db.models import Role, UserRole  # noqa: E402

client = TestClient(app)


Base.metadata.create_all(bind=engine)


def test_assign_and_protected_access() -> None:
    """User with assigned role can access endpoints."""
    admin_token = create_access_token({"sub": "u1"})
    viewer_token = create_access_token({"sub": "u2"})

    with session_scope() as session:
        admin_role = Role(id=1, name="admin")
        session.add_all(
            [
                admin_role,
                Role(id=2, name="editor"),
                Role(id=3, name="viewer"),
            ]
        )
        session.flush()
        session.add(
            UserRole(
                user_id="u1",
                role=admin_role,
            )
        )

    resp = client.post(
        "/roles/assign",
        json={"user_id": "u2", "role": "viewer"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200

    resp = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 200
