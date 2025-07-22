"""Ensure revoked JWT tokens are rejected."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend" / "analytics"))

from backend.analytics import api  # noqa: E402
from backend.analytics.auth import (
    create_access_token,
    verify_token,
)
from backend.shared.db import SessionLocal  # noqa: E402
from backend.shared.db.models import RevokedToken, UserRole  # noqa: E402
from fastapi.security import HTTPAuthorizationCredentials

client = TestClient(api.app)


def test_revoked_token_rejected() -> None:
    """Access is denied when the token is revoked."""
    token = create_access_token({"sub": "admin"})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    payload = verify_token(credentials)
    jti = str(payload["jti"])
    expires_at = datetime.now(UTC) + timedelta(minutes=30)
    with SessionLocal() as session:
        session.add(UserRole(username="admin", role="admin"))
        session.add(RevokedToken(jti=jti, expires_at=expires_at))
        session.commit()
    resp = client.get(
        "/marketplace_metrics/1/export",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Token revoked"
