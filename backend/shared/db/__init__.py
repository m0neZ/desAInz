"""Database utilities shared across services."""

from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from typing import Any, Iterator, AsyncIterator
import asyncio
import os
from alembic import command
from alembic.config import Config

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .base import Base
from backend.shared.config import settings

SKIP_MIGRATIONS_ENV = "SKIP_MIGRATIONS"

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "session_scope",
    "async_engine",
    "AsyncSessionLocal",
    "async_session_scope",
]

DATABASE_URL = str(settings.effective_database_url)

if DATABASE_URL.startswith("sqlite") and "+" not in DATABASE_URL:
    ASYNC_DATABASE_URL = DATABASE_URL.replace("sqlite", "sqlite+aiosqlite", 1)
elif DATABASE_URL.startswith("postgresql") and "+" not in DATABASE_URL:
    ASYNC_DATABASE_URL = DATABASE_URL.replace(
        "postgresql",
        "postgresql+asyncpg",
        1,
    )
else:
    ASYNC_DATABASE_URL = DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)


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


@asynccontextmanager
async def async_session_scope(
    username: str | None = None,
) -> AsyncIterator[AsyncSession]:
    """Asynchronous transactional session scope."""
    session: AsyncSession = AsyncSessionLocal()

    if username is not None:

        @event.listens_for(session.sync_session, "after_begin")  # type: ignore[misc]
        def _set_username(
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
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def run_migrations_if_needed(config_path: str) -> None:
    """Upgrade the database to the latest revision when required."""
    if os.getenv(SKIP_MIGRATIONS_ENV) in {"1", "true", "True"}:
        return

    cfg = Config(config_path)
    cfg.set_main_option("sqlalchemy.url", str(settings.effective_database_url))
    await asyncio.to_thread(command.upgrade, cfg, "head")


__all__.append("run_migrations_if_needed")
