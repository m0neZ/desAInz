"""Tests for the privacy purge job."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from dagster import DagsterInstance
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

ROOT = Path(__file__).resolve().parents[3]
ORCHESTRATOR_PATH = ROOT / "backend" / "orchestrator"
sys.path.append(str(ORCHESTRATOR_PATH))  # noqa: E402
MONITORING_SRC = ROOT / "backend" / "monitoring" / "src"
sys.path.append(str(MONITORING_SRC))  # noqa: E402
SIGNAL_SRC = ROOT / "backend" / "signal-ingestion" / "src"
sys.path.append(str(SIGNAL_SRC))  # noqa: E402

from orchestrator.jobs import privacy_purge_job  # noqa: E402
from signal_ingestion import database  # noqa: E402
from signal_ingestion.models import Signal  # noqa: E402


@pytest.mark.asyncio()  # type: ignore[misc]
async def test_privacy_purge_job(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure the job removes PII from stored signals."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    database.engine = engine
    database.SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    await database.init_db()

    async with database.SessionLocal() as session:
        session.add(
            Signal(
                source="t",
                content="Contact me at user@example.com",
                embedding=[0.0],
            )
        )
        await session.commit()

    monkeypatch.setattr(
        "signal_ingestion.privacy.SessionLocal",
        database.SessionLocal,
        raising=False,
    )

    instance = DagsterInstance.ephemeral()
    result = privacy_purge_job.execute_in_process(instance=instance)
    assert result.success

    async with database.SessionLocal() as session:
        row = (await session.execute(select(Signal))).scalars().first()
        assert "[REDACTED]" in row.content
