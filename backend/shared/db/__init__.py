"""Database utilities shared across services."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from .base import Base
from backend.shared.config import settings

__all__ = ["Base", "engine", "SessionLocal", "session_scope"]

DATABASE_URL = settings.database_url
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def session_scope(username: str | None = None) -> Iterator[Session]:
    """Return a transactional scope optionally setting RLS user."""
    session: Session = SessionLocal()
    if username is not None:
        session.execute(
            text("SET LOCAL app.current_username = :user"), {"user": username}
        )
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
