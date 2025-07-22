"""Tests for audit logging."""

from __future__ import annotations

from pathlib import Path
import sys
import warnings

sys.path.append(
    str(Path(__file__).resolve().parents[1] / "backend" / "api-gateway" / "src")
)

import importlib.util

audit_path = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "api-gateway"
    / "src"
    / "api_gateway"
    / "audit.py"
)
spec = importlib.util.spec_from_file_location("api_gateway.audit", audit_path)
audit = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(audit)
log_admin_action = audit.log_admin_action
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Iterator

import pytest

from backend.shared.db import Base  # noqa: E402
from backend.shared.db.models import AuditLog  # noqa: E402

SessionLocal = sessionmaker()


@pytest.fixture(autouse=True)
def _audit_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Provide isolated database for audit tests."""
    db_path = tmp_path / "audit.db"
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    SessionLocal = sessionmaker(bind=engine, future=True)
    globals()["SessionLocal"] = SessionLocal
    monkeypatch.setattr("backend.shared.db.SessionLocal", SessionLocal, raising=False)
    monkeypatch.setattr("backend.shared.db.engine", engine, raising=False)
    Base.metadata.create_all(engine)
    try:
        yield
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_log_admin_action_persists() -> None:
    """Audit entries should persist after logging."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        log_admin_action("alice", "login", {"ip": "127.0.0.1"})
    with SessionLocal() as session:
        logs = session.query(AuditLog).all()
        assert len(logs) == 1
        log = logs[0]
        assert log.username == "alice"
        assert log.action == "login"
        assert log.details == {"ip": "127.0.0.1"}
