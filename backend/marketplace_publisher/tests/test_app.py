# flake8: noqa
"""Tests for marketplace publisher API."""

from __future__ import annotations

import os

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test.db"

from marketplace_publisher.db import engine
from marketplace_publisher.main import app
from marketplace_publisher.models import Base


@pytest.mark.asyncio
async def test_publish(monkeypatch) -> None:
    """Publishing returns job info."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def dummy_publish(*args, **kwargs):
        return "123"

    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    async def test_session():
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session() as session:
            yield session

    monkeypatch.setattr("marketplace_publisher.main.get_session", test_session)
    monkeypatch.setattr("marketplace_publisher.main._publish", dummy_publish)
    transport = ASGITransport(app=app)
    async with LifespanManager(app):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res = await ac.post("/publish/redbubble", json={"title": "hi"})
    assert res.status_code == 200
    assert res.json()["listing_id"] == "123"
