"""Tests for publisher rejection scenarios."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import fakeredis.aioredis
import pytest
from fastapi.testclient import TestClient
from marketplace_publisher import db, publisher
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.mark.asyncio()
async def test_publish_trademark_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Return ``nsfw`` when the design is trademarked."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(db, "SessionLocal", session_factory)
    await db.init_db()

    class DummyClient:
        def publish_design(self, design_path: Path, metadata: dict[str, Any]) -> str:
            return "ok"

    publisher.CLIENTS[db.Marketplace.redbubble] = DummyClient()
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
    """Return ``nsfw`` when the image violates policy."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(db, "SessionLocal", session_factory)
    await db.init_db()

    class DummyClient:
        def publish_design(self, design_path: Path, metadata: dict[str, Any]) -> str:
            return "ok"

    publisher.CLIENTS[db.Marketplace.redbubble] = DummyClient()
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


def test_api_trademark_failure(monkeypatch: Any, tmp_path: Path) -> None:
    """Return HTTP 400 when the title is trademarked."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    from marketplace_publisher.db import Marketplace
    from marketplace_publisher.main import app, rate_limiter

    rate_limiter._redis = fakeredis.aioredis.FakeRedis()

    class DummyClient:
        def publish_design(self, design_path: Path, metadata: dict[str, Any]) -> str:
            return "ok"

    publisher.CLIENTS[Marketplace.redbubble] = DummyClient()

    async def _noop(*args: Any, **kwargs: Any) -> None:
        return None

    publisher._fallback.publish = _noop
    monkeypatch.setattr(publisher, "is_trademarked", lambda term: True)
    monkeypatch.setattr(publisher, "ensure_not_nsfw", lambda img: None)

    with TestClient(app) as client:
        design = tmp_path / "img.png"
        design.write_text("img")
        resp = client.post(
            "/publish",
            json={
                "marketplace": Marketplace.redbubble.value,
                "design_path": str(design),
                "metadata": {"title": "foo"},
            },
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "trademarked"


def test_api_nsfw_failure(monkeypatch: Any, tmp_path: Path) -> None:
    """Return HTTP 400 when the image is flagged NSFW."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    from marketplace_publisher.db import Marketplace
    from marketplace_publisher.main import app, rate_limiter

    rate_limiter._redis = fakeredis.aioredis.FakeRedis()

    class DummyClient:
        def publish_design(self, design_path: Path, metadata: dict[str, Any]) -> str:
            return "ok"

    publisher.CLIENTS[Marketplace.redbubble] = DummyClient()

    async def _noop2(*args: Any, **kwargs: Any) -> None:
        return None

    publisher._fallback.publish = _noop2
    monkeypatch.setattr(publisher, "is_trademarked", lambda term: False)

    def raise_nsfw(img: Any) -> None:  # noqa: ANN001
        raise ValueError("NSFW")

    monkeypatch.setattr(publisher, "ensure_not_nsfw", raise_nsfw)

    with TestClient(app) as client:
        design = tmp_path / "img.png"
        design.write_text("img")
        resp = client.post(
            "/publish",
            json={
                "marketplace": Marketplace.redbubble.value,
                "design_path": str(design),
                "metadata": {},
            },
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "nsfw"
