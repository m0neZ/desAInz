"""Tests for publishing logic with Selenium fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import requests

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from marketplace_publisher import db, publisher


@pytest.mark.asyncio()
async def test_fallback_invoked_on_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Fallback upload should run when API publishing fails."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(db, "SessionLocal", session_factory)
    await db.init_db()

    called: dict[str, bool] = {"fallback": False}

    class FailingClient:
        def publish_design(self, design_path: Path, metadata: dict[str, Any]) -> str:
            raise requests.RequestException("boom")

    publisher.CLIENTS[db.Marketplace.redbubble] = FailingClient()  # type: ignore[assignment]
    monkeypatch.setattr(
        publisher._fallback,
        "publish",
        lambda *a, **k: called.__setitem__("fallback", True),
    )

    async with session_factory() as session:
        task = await db.create_task(
            session,
            marketplace=db.Marketplace.redbubble,
            design_path=str(tmp_path / "d.png"),
        )
        (tmp_path / "d.png").write_text("img")
        await publisher.publish_with_retry(
            session, task.id, db.Marketplace.redbubble, tmp_path / "d.png", {}
        )

    assert called["fallback"]
