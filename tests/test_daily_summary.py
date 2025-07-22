"""Tests for daily summary script."""

from __future__ import annotations

import sys
from pathlib import Path
import json

sys.path.append(
    str(
        Path(__file__).resolve().parents[1]
        / "backend"
        / "marketplace-publisher"
        / "src"
    )
)

import pytest
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.shared.db import Base
from scripts.daily_summary import generate_daily_summary


@pytest.mark.asyncio
async def test_generate_daily_summary(tmp_path: Path) -> None:
    """Summary returns all expected keys."""
    from unittest.mock import AsyncMock, patch

    with patch(
        "scripts.daily_summary._marketplace_stats", new=AsyncMock(return_value={})
    ):
        engine = create_engine("sqlite:///:memory:", future=True)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine, future=True)

        @contextmanager
        def provider() -> Session:
            session: Session = SessionLocal()
            try:
                yield session
            finally:
                session.close()

        output = tmp_path / "report.json"
        result = await generate_daily_summary(
            session_provider=provider, output_file=output
        )
    assert "ideas_generated" in result
    assert "mockup_success_rate" in result
    assert "marketplace_stats" in result
    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8")) == result
