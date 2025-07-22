"""Tests for the privacy purge endpoint."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from api_gateway.main import app  # noqa: E402
from api_gateway.auth import create_access_token  # noqa: E402
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


async def _dummy_purge(limit=None):
    return 5


def test_purge_pii_endpoint(monkeypatch):
    """Trigger PII purge and return count."""
    monkeypatch.setattr("signal_ingestion.privacy.purge_pii_rows", _dummy_purge)
    token = create_access_token({"sub": "admin"})
    resp = client.delete(
        "/privacy/signals?limit=2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "purged": 5}
