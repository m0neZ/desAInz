"""Verify row-level security policies on user tables."""

from __future__ import annotations


from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from testing.postgresql import Postgresql
from datetime import datetime, UTC


def test_rls_enforcement() -> None:
    """Ensure users can only see their own rows."""
    with Postgresql() as pg:
        url = pg.url()
        cfg = Config("backend/shared/db/alembic_api_gateway.ini")
        cfg.set_main_option("sqlalchemy.url", url)
        command.upgrade(cfg, "head")
        cfg = Config("backend/shared/db/alembic_scoring_engine.ini")
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
            idea_id = session.execute(
                text(
                    """
                    INSERT INTO ideas (username, title, description, created_at)
                    VALUES ('alice', 't', 'd', :ts)
                    RETURNING id
                    """
                ),
                {"ts": datetime.now(UTC)},
            ).scalar_one()
            session.execute(
                text(
                    """
                    INSERT INTO refresh_tokens (token, username, expires_at)
                    VALUES ('tok', 'alice', now())
                    """
                )
            )
            session.execute(
                text(
                    """
                    INSERT INTO mockups (idea_id, image_url, created_at, username)
                    VALUES (:idea_id, 'u', now(), 'alice')
                    """
                ),
                {"idea_id": idea_id},
            )
            session.execute(
                text(
                    """
                    INSERT INTO signals (username, idea_id, timestamp, engagement_rate)
                    VALUES ('alice', :idea_id, now(), 1.0)
                    """
                ),
                {"idea_id": idea_id},
            )
            session.commit()

        with Session() as session:
            session.execute(text("SET LOCAL app.current_username = 'bob'"))
            assert session.execute(text("SELECT * FROM audit_logs")).fetchall() == []
            assert session.execute(text("SELECT * FROM ideas")).fetchall() == []
            assert session.execute(text("SELECT * FROM signals")).fetchall() == []
            assert (
                session.execute(text("SELECT * FROM refresh_tokens")).fetchall() == []
            )
            assert session.execute(text("SELECT * FROM mockups")).fetchall() == []
