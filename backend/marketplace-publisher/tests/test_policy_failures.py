"""Tests for publisher rejection scenarios."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import asyncio

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from fastapi.testclient import TestClient
import fakeredis.aioredis
from marketplace_publisher import publisher, db
from tests.utils import return_none, return_true, return_false


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

    publisher.CLIENTS[db.Marketplace.redbubble] = DummyClient()  # type: ignore[assignment]
    monkeypatch.setattr(publisher, "is_trademarked", return_true)
    monkeypatch.setattr(publisher, "ensure_not_nsfw", return_none)
    pd_calls: list[tuple[int, str]] = []
    monkeypatch.setattr(
        publisher, "notify_listing_issue", lambda *a: pd_calls.append(a)
    )
    monkeypatch.setattr(asyncio, "to_thread", lambda func, *a, **kw: func(*a, **kw))

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
    assert pd_calls == [(task.id, "trademarked")]


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

    publisher.CLIENTS[db.Marketplace.redbubble] = DummyClient()  # type: ignore[assignment]
    monkeypatch.setattr(publisher, "is_trademarked", return_false)

    def raise_nsfw(img: Any) -> None:  # noqa: ANN001
        raise ValueError("NSFW")

    monkeypatch.setattr(publisher, "ensure_not_nsfw", raise_nsfw)
    pd_calls_2: list[tuple[int, str]] = []
    monkeypatch.setattr(
        publisher, "notify_listing_issue", lambda *a: pd_calls_2.append(a)
    )
    monkeypatch.setattr(asyncio, "to_thread", lambda func, *a, **kw: func(*a, **kw))

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
    assert pd_calls_2 == [(task.id, "nsfw")]


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

    publisher.CLIENTS[Marketplace.redbubble] = DummyClient()  # type: ignore[assignment]

    async def _noop(*args: Any, **kwargs: Any) -> None:
        return None

    publisher._fallback.publish = _noop  # type: ignore[method-assign]
    monkeypatch.setattr(publisher, "is_trademarked", return_true)
    monkeypatch.setattr(publisher, "ensure_not_nsfw", return_none)

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

    publisher.CLIENTS[Marketplace.redbubble] = DummyClient()  # type: ignore[assignment]

    async def _noop2(*args: Any, **kwargs: Any) -> None:
        return None

    publisher._fallback.publish = _noop2  # type: ignore[method-assign]
    monkeypatch.setattr(publisher, "is_trademarked", return_false)

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
