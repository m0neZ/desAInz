"""Database utilities shared across services."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from .base import Base
from backend.shared.config import settings

__all__ = ["Base", "engine", "SessionLocal", "session_scope"]

DATABASE_URL = settings.effective_database_url
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def session_scope(username: str | None = None) -> Iterator[Session]:
    """
    Return a transactional scope optionally setting RLS user.

    When ``username`` is provided, the ``app.current_username`` setting is
    configured on every transaction so that row-level security policies relying
    on it are consistently enforced.
    """
    session: Session = SessionLocal()

    if username is not None:

        @event.listens_for(session, "after_begin")  # type: ignore[misc]
        def _set_username(  # noqa: D401 -- event listener, not a docstring
            _session: Session,
            _transaction: Any,
            connection: Any,
        ) -> None:
            connection.execute(
                text("SET LOCAL app.current_username = :user"),
                {"user": username},
            )

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
