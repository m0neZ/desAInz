"""Tests for Alembic migrations."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(REPO_ROOT))
sys.path.append(str(REPO_ROOT / "backend" / "api-gateway" / "src"))
sys.path.append(str(REPO_ROOT / "backend" / "marketplace-publisher" / "src"))
sys.path.append(str(REPO_ROOT / "backend" / "signal-ingestion" / "src"))

import pytest
from alembic import command
from alembic.config import Config

from tests.utils import assert_single_head


def _run_migration(config_path: str, tmp_path: Path) -> None:
    """Upgrade and downgrade a migration chain."""
    db_path = tmp_path / "test.db"
    cfg = Config(config_path)
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")


@pytest.mark.parametrize(
    "config_path",
    [
        "backend/shared/db/alembic_scoring_engine.ini",
        "backend/shared/db/alembic_api_gateway.ini",
        "backend/shared/db/alembic_marketplace_publisher.ini",
        "backend/shared/db/alembic_signal_ingestion.ini",
        "backend/shared/db/alembic_mockup_generation.ini",
    ],
)
def test_migrations(config_path: str, tmp_path: Path) -> None:
    """Ensure migrations apply cleanly for each service."""
    _run_migration(config_path, tmp_path)


@pytest.mark.parametrize(
    "config_path",
    [
        "backend/shared/db/alembic_scoring_engine.ini",
        "backend/shared/db/alembic_api_gateway.ini",
        "backend/shared/db/alembic_marketplace_publisher.ini",
        "backend/shared/db/alembic_signal_ingestion.ini",
        "backend/shared/db/alembic_mockup_generation.ini",
    ],
)
def test_single_head(config_path: str) -> None:
    """Ensure each environment has a single Alembic head."""
    assert_single_head(config_path)
