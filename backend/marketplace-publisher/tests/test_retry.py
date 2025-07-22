"""Tests for background retry logic."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT))
import os
import warnings

import requests
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

warnings.filterwarnings("ignore", category=DeprecationWarning)

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from marketplace_publisher import db, main, notifications, publisher
from marketplace_publisher.settings import settings


@pytest.mark.asyncio()
async def test_retry_on_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Retry publishing when the first attempt fails."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(db, "SessionLocal", session_factory)
    monkeypatch.setattr(settings, "max_attempts", 2)
    await db.init_db()

    calls: dict[str, int] = {"count": 0}

    class FlakyClient:
        def publish_design(self, design_path: Path, metadata: dict[str, Any]) -> str:
            calls["count"] += 1
            if calls["count"] == 1:
                raise requests.RequestException("boom")
            return "ok"

    publisher.CLIENTS[
        db.Marketplace.redbubble
    ] = FlakyClient()  # type: ignore[assignment]

    scheduled: list[asyncio.Future[Any]] = []

    async def immediate(coro: asyncio.coroutines.Coroutine[Any, Any, Any]) -> None:
        fut = asyncio.create_task(coro)
        scheduled.append(fut)
        await fut

    monkeypatch.setattr(asyncio, "create_task", immediate)

    async with session_factory() as session:
        task = await db.create_task(
            session,
            marketplace=db.Marketplace.redbubble,
            design_path=str(tmp_path / "d.png"),
        )
        (tmp_path / "d.png").write_text("img")

    await main._background_publish(task.id)
    assert calls["count"] == 2
    async with session_factory() as session:
        refreshed = await db.get_task(session, task.id)
        assert refreshed.status == db.PublishStatus.success


@pytest.mark.asyncio()
async def test_publish_notifies_after_max_attempts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Failure after max attempts should trigger notifications."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(db, "SessionLocal", session_factory)
    await db.init_db()

    class FailingClient:
        def publish_design(self, design_path: Path, metadata: dict[str, Any]) -> str:
            raise requests.RequestException("boom")

    publisher.CLIENTS[db.Marketplace.redbubble] = FailingClient()  # type: ignore[assignment]

    notified: list[tuple[int, str]] = []
    monkeypatch.setattr(
        notifications,
        "notify_failure",
        lambda task_id, marketplace: notified.append((task_id, marketplace)),
    )

    async with session_factory() as session:
        task = await db.create_task(
            session,
            marketplace=db.Marketplace.redbubble,
            design_path=str(tmp_path / "img.png"),
        )
        (tmp_path / "img.png").write_text("img")
        await publisher.publish_with_retry(
            session,
            task.id,
            db.Marketplace.redbubble,
            tmp_path / "img.png",
            {},
            max_attempts=1,
        )

    assert notified == [(task.id, db.Marketplace.redbubble.value)]
