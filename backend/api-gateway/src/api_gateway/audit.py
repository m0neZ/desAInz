"""Audit logging utilities."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.shared.db import session_scope
from backend.shared.db.models import AuditLog


def log_admin_action(
    username: str, action: str, details: dict[str, Any] | None = None
) -> None:
    """Persist an admin action to the audit log."""
    with session_scope() as session:
        session.add(
            AuditLog(
                username=username,
                action=action,
                details=details,
                timestamp=datetime.utcnow(),
            )
        )
        session.flush()
        session.commit()
