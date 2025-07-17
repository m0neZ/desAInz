"""Verify row-level security policies on user tables."""

from __future__ import annotations


from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from testing.postgresql import Postgresql


def test_rls_enforcement() -> None:
    """Ensure users can only see their own rows."""
    with Postgresql() as pg:
        url = pg.url()
        cfg = Config("backend/shared/db/alembic_api_gateway.ini")
        cfg.set_main_option("sqlalchemy.url", url)
        command.upgrade(cfg, "head")

        engine = create_engine(url, future=True)
        Session = sessionmaker(bind=engine, future=True)

        with Session() as session:
            session.execute(text("SET LOCAL app.current_username = 'alice'"))
            session.execute(
                text(
                    """
                    INSERT INTO audit_logs (username, action, timestamp)
                    VALUES ('alice', 'login', now())
                    """
                )
            )
            session.commit()

        with Session() as session:
            session.execute(text("SET LOCAL app.current_username = 'bob'"))
            result = session.execute(text("SELECT * FROM audit_logs")).fetchall()
            assert result == []
