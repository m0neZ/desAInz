"""Tests for manual maintenance trigger."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from api_gateway.auth import create_access_token  # noqa: E402
from api_gateway.main import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.shared.db import Base, engine, session_scope  # noqa: E402
from backend.shared.db.models import UserRole  # noqa: E402
from scripts import maintenance  # noqa: E402

client = TestClient(app)


def setup_module(module: object) -> None:
    """Prepare database tables."""
    Base.metadata.create_all(engine)
    with session_scope() as session:
        session.add(UserRole(username="admin", role="admin"))


def teardown_module(module: object) -> None:
    """Drop tables after tests."""
    Base.metadata.drop_all(engine)


def test_trigger_cleanup(monkeypatch) -> None:
    """Manual trigger should invoke maintenance functions."""
    called: dict[str, bool] = {}

    def mark_archive() -> None:
        called["archive"] = True

    def mark_purge() -> None:
        called["purge"] = True

    monkeypatch.setattr(maintenance, "archive_old_mockups", mark_archive)
    monkeypatch.setattr(maintenance, "purge_stale_records", mark_purge)
    token = create_access_token({"sub": "admin"})
    resp = client.post(
        "/maintenance/cleanup",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert called == {"archive": True, "purge": True}
