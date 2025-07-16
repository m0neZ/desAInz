"""Admin action auditing utilities."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import delete, select

from backend.shared.db import session_scope, engine
from backend.shared.db.base import Base
from backend.shared.db.models import AuditLog


Base.metadata.create_all(engine)


scheduler = BackgroundScheduler()


def record_action(admin_id: str, action: str) -> None:
    """Persist an administrator action."""
    with session_scope() as session:
        session.add(
            AuditLog(
                admin_id=admin_id,
                action=action,
                created_at=datetime.now(UTC),
            )
        )


def get_logs(page: int, limit: int) -> list[dict[str, str]]:
    """Return paginated audit log entries."""
    with session_scope() as session:
        stmt = (
            select(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        rows = session.execute(stmt).scalars().all()
        return [
            {
                "admin_id": row.admin_id,
                "action": row.action,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]


def purge_old_logs(months: int = 18) -> None:
    """Delete audit log entries older than ``months`` months."""
    threshold = datetime.now(UTC) - timedelta(days=months * 30)
    with session_scope() as session:
        session.execute(delete(AuditLog).where(AuditLog.created_at < threshold))


def start_retention_scheduler() -> None:
    """Start background job for purging old logs."""
    if not scheduler.running:
        scheduler.add_job(purge_old_logs, "cron", hour=0, minute=0)
        scheduler.start()
