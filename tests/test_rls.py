"""Verify row-level security policies on user tables."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Callable, Iterable, Iterator, List

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, create_engine, text
from sqlalchemy.orm import Session, sessionmaker
import uuid

ADMIN_URL = "postgresql://postgres@localhost/postgres"


def _create_db() -> tuple[str, Callable[[], None]]:
    """Create a temporary database and return its URL and cleanup callback."""

    db_name = f"test_{uuid.uuid4().hex}"
    admin_engine = create_engine(ADMIN_URL, future=True)
    with admin_engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT").execute(
            text(f'CREATE DATABASE "{db_name}"')
        )

    def _drop() -> None:
        with admin_engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT").execute(
                text(f'DROP DATABASE IF EXISTS "{db_name}"')
            )

    return f"postgresql://postgres@localhost/{db_name}", _drop


def _rls_tables(conn: Connection) -> List[str]:
    """Return all tables with row-level security policies."""

    result = conn.execute(
        text("SELECT DISTINCT tablename FROM pg_policies WHERE schemaname='public'")
    )
    return [row.tablename for row in result]


def _insert_row(session: Session, table_name: str) -> None:
    """Insert a row owned by ``alice`` into ``table_name``."""

    session.execute(text("SET LOCAL app.current_username = 'alice'"))
    if table_name == "user_roles":
        session.execute(
            text("INSERT INTO user_roles (username, role) VALUES ('alice', 'admin')")
        )
    elif table_name == "audit_logs":
        session.execute(
            text(
                "INSERT INTO audit_logs (username, action, timestamp)"
                " VALUES ('alice', 'login', now())"
            )
        )
    elif table_name == "ideas":
        session.execute(
            text(
                "INSERT INTO ideas (username, title, description, created_at)"
                " VALUES ('alice', 't', 'd', :ts)"
            ),
            {"ts": datetime.now(UTC)},
        )
    elif table_name == "signals":
        idea_id = session.execute(
            text(
                "INSERT INTO ideas (username, title, description, created_at)"
                " VALUES ('alice', 't', 'd', :ts) RETURNING id"
            ),
            {"ts": datetime.now(UTC)},
        ).scalar_one()
        session.execute(
            text(
                "INSERT INTO signals (username, idea_id, timestamp, engagement_rate)"
                " VALUES ('alice', :idea_id, now(), 1.0)"
            ),
            {"idea_id": idea_id},
        )
    elif table_name == "refresh_tokens":
        session.execute(
            text(
                "INSERT INTO refresh_tokens (token, username, expires_at) "
                "VALUES ('t', 'alice', now())"
            )
        )
    else:  # pragma: no cover - safeguard for future tables
        raise ValueError(f"Unhandled RLS table {table_name}")
    session.commit()


@pytest.mark.parametrize(
    "table_name",
    ["audit_logs", "ideas", "signals", "user_roles", "refresh_tokens"],
)
def test_rls_enforcement(table_name: str) -> None:
    """Ensure users cannot view each other's rows."""

    url, cleanup = _create_db()
    cfg = Config("backend/shared/db/alembic_api_gateway.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    cfg = Config("backend/shared/db/alembic_scoring_engine.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    engine = create_engine(url, future=True)
    Session = sessionmaker(bind=engine, future=True)

    with Session() as session:
        _insert_row(session, table_name)

    with Session() as session:
        session.execute(text("SET LOCAL app.current_username = 'bob'"))
        rows = session.execute(text(f"SELECT * FROM {table_name}")).fetchall()
        assert rows == []

    cleanup()


def test_identify_rls_tables() -> None:
    """Identify all tables protected by row-level security."""

    url, cleanup = _create_db()
    cfg = Config("backend/shared/db/alembic_api_gateway.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    cfg = Config("backend/shared/db/alembic_scoring_engine.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    engine = create_engine(url, future=True)
    with engine.connect() as conn:
        tables = _rls_tables(conn)

    expected = ["audit_logs", "ideas", "signals", "user_roles", "refresh_tokens"]
    assert set(tables) == set(expected)

    cleanup()
