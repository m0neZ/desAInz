"""Tests for audit logging."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api_gateway.main import app
from api_gateway.auth import create_access_token
from api_gateway.audit import purge_old_logs
from pytest import MonkeyPatch
from backend.shared.db import engine
from backend.shared.db.base import Base


Base.metadata.create_all(engine)

client = TestClient(app)


def test_audit_log_flow(monkeypatch: MonkeyPatch) -> None:
    """Admin actions should be recorded and retrieved."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    purge_old_logs()
    token = create_access_token({"sub": "admin"})
    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    response = client.get("/admin/logs", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["logs"][0]["admin_id"] == "admin"
