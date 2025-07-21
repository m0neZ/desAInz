from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from marketplace_publisher import publisher, db
from marketplace_publisher.settings import settings


@pytest.mark.asyncio()
async def test_publish_trademark_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(db, "SessionLocal", session_factory)
    await db.init_db()

    class DummyClient:
        def publish_design(self, design_path: Path, metadata: dict[str, Any]) -> str:
            return "ok"

    publisher.CLIENTS[db.Marketplace.redbubble] = DummyClient()  # type: ignore[assignment]
    monkeypatch.setattr(publisher, "is_trademarked", lambda term: True)
    monkeypatch.setattr(publisher, "ensure_not_nsfw", lambda img: None)

    async with session_factory() as session:
        task = await db.create_task(
            session,
            marketplace=db.Marketplace.redbubble,
            design_path=str(tmp_path / "img.png"),
        )
        (tmp_path / "img.png").write_text("img")
        result = await publisher.publish_with_retry(
            session,
            task.id,
            db.Marketplace.redbubble,
            tmp_path / "img.png",
            {"title": "foo"},
            max_attempts=1,
        )
    assert result == "trademarked"


@pytest.mark.asyncio()
async def test_publish_nsfw_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(db, "SessionLocal", session_factory)
    await db.init_db()

    class DummyClient:
        def publish_design(self, design_path: Path, metadata: dict[str, Any]) -> str:
            return "ok"

    publisher.CLIENTS[db.Marketplace.redbubble] = DummyClient()  # type: ignore[assignment]
    monkeypatch.setattr(publisher, "is_trademarked", lambda term: False)

    def raise_nsfw(img: Any) -> None:  # noqa: ANN001
        raise ValueError("NSFW")

    monkeypatch.setattr(publisher, "ensure_not_nsfw", raise_nsfw)

    async with session_factory() as session:
        task = await db.create_task(
            session,
            marketplace=db.Marketplace.redbubble,
            design_path=str(tmp_path / "img.png"),
        )
        (tmp_path / "img.png").write_text("img")
        result = await publisher.publish_with_retry(
            session,
            task.id,
            db.Marketplace.redbubble,
            tmp_path / "img.png",
            {},
            max_attempts=1,
        )
    assert result == "nsfw"
