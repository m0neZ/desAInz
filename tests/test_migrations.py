"""Tests for Alembic migrations."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_scoring_engine_migrations(tmp_path: Path) -> None:
    """Apply and revert scoring engine migrations without errors."""
    db_path = tmp_path / "test.db"
    cfg = Config("backend/shared/db/alembic_scoring_engine.ini")
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

    command.upgrade(cfg, "head")

    engine = create_engine(f"sqlite:///{db_path}")
    insp = inspect(engine)
    assert "score_metrics" in insp.get_table_names()
    assert "publish_latency_metrics" in insp.get_table_names()

    command.downgrade(cfg, "base")

    insp = inspect(engine)
    assert "score_metrics" not in insp.get_table_names()
    assert "publish_latency_metrics" not in insp.get_table_names()
