"""Tests for audit logging."""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

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
from backend.shared.db import Base, SessionLocal, engine  # noqa: E402
from backend.shared.db.models import AuditLog  # noqa: E402


def setup_module(module: object) -> None:
    """Create tables for tests."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        Base.metadata.create_all(engine)


def teardown_module(module: object) -> None:
    """Drop tables after tests."""
    Base.metadata.drop_all(engine)


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
