"""Validation error tests for API endpoints."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

# API Gateway setup
sys.path.append(
    str(Path(__file__).resolve().parents[1] / "backend" / "api-gateway" / "src")
)
from api_gateway.main import app as gateway_app  # noqa: E402
from api_gateway.auth import create_access_token  # noqa: E402
from backend.shared.db import session_scope  # noqa: E402
from backend.shared.db.models import UserRole  # noqa: E402

client = TestClient(gateway_app)


def test_issue_token_validation() -> None:
    """Missing username should return validation error."""
    resp = client.post("/auth/token", json={})
    assert resp.status_code == 422


def test_assign_role_validation() -> None:
    """Invalid request body should raise 422."""
    token = create_access_token({"sub": "admin"})
    with session_scope() as session:
        session.add(UserRole(username="admin", role="admin"))
        session.flush()
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post("/roles/test", headers=headers, json={})
    assert resp.status_code == 422


# Marketplace publisher setup
sys.path.append(
    str(
        Path(__file__).resolve().parents[1]
        / "backend"
        / "marketplace-publisher"
        / "src"
    )
)
from marketplace_publisher import main as mp_main  # noqa: E402

publisher_client = TestClient(mp_main.app)


@pytest.mark.asyncio()
async def test_update_task_metadata_validation(monkeypatch, tmp_path: Path) -> None:
    """Non-object metadata payload should be rejected."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    monkeypatch.setattr(
        mp_main, "engine", create_async_engine("sqlite+aiosqlite:///:memory:")
    )
    session_factory = async_sessionmaker(mp_main.engine, expire_on_commit=False)
    monkeypatch.setattr(mp_main, "SessionLocal", session_factory)
    await mp_main.init_db()
    async with session_factory() as session:
        task = await mp_main.create_task(
            session,
            marketplace=mp_main.Marketplace.redbubble,
            design_path="design.png",
        )
    resp = publisher_client.patch(f"/tasks/{task.id}", json=[])
    assert resp.status_code == 422
