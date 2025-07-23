"""Tests for webhook handling in marketplace publisher."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import warnings
from pathlib import Path

# isort: off
from fastapi.testclient import TestClient
from marketplace_publisher import db  # noqa: E402
from marketplace_publisher import main  # noqa: E402

import pytest

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

# isort: on


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "backend" / "marketplace-publisher" / "src"))  # noqa: E402
sys.path.append(str(ROOT))  # noqa: E402

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"  # noqa: E402
os.environ["SELENIUM_SKIP"] = "1"  # noqa: E402


@pytest.mark.asyncio()
async def test_webhook_updates_task_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sqlite_engine: AsyncEngine,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Posting to the webhook should update task status."""
    monkeypatch.setattr(db, "engine", sqlite_engine)
    monkeypatch.setattr(db, "SessionLocal", session_factory)
    from datetime import UTC, datetime
    from types import SimpleNamespace

    monkeypatch.setattr(
        db,
        "datetime",
        SimpleNamespace(utcnow=lambda: datetime.now(UTC)),
    )
    await db.init_db()

    async with session_factory() as session:
        now = datetime.now(UTC)
        task = await db.create_task(
            session,
            marketplace=db.Marketplace.redbubble,
            design_path="design.png",
            created_at=now,
            updated_at=now,
        )

    client = TestClient(main.app)
    resp = client.post(
        f"/webhooks/{db.Marketplace.redbubble.value}",
        json={"task_id": task.id, "status": db.PublishStatus.success.value},
    )
    assert resp.status_code == 200

    async with session_factory() as session:
        refreshed = await db.get_task(session, task.id)
        assert refreshed is not None
        assert refreshed.status == db.PublishStatus.success
        events = (
            await session.execute(
                select(db.WebhookEvent).where(db.WebhookEvent.task_id == task.id)
            )
        ).scalars()
        assert len(list(events)) == 1


@pytest.mark.asyncio()
async def test_webhook_requires_signature(
    monkeypatch: pytest.MonkeyPatch,
    sqlite_engine: AsyncEngine,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Webhook calls without a signature should be rejected."""
    monkeypatch.setattr(db, "engine", sqlite_engine)
    monkeypatch.setattr(db, "SessionLocal", session_factory)
    await db.init_db()

    async with session_factory() as session:
        task = await db.create_task(
            session,
            marketplace=db.Marketplace.redbubble,
            design_path="img.png",
        )

    client = TestClient(main.app)
    resp = client.post(
        f"/webhooks/{db.Marketplace.redbubble.value}",
        json={"task_id": task.id, "status": db.PublishStatus.success.value},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio()
async def test_webhook_valid_signature(
    monkeypatch: pytest.MonkeyPatch,
    sqlite_engine: AsyncEngine,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Valid ``X-Signature`` header should authenticate the request."""
    monkeypatch.setattr(db, "engine", sqlite_engine)
    monkeypatch.setattr(db, "SessionLocal", session_factory)
    monkeypatch.setenv("WEBHOOK_SECRET_REDBUBBLE", "secret")
    await db.init_db()

    async with session_factory() as session:
        task = await db.create_task(
            session,
            marketplace=db.Marketplace.redbubble,
            design_path="x.png",
        )

    payload = {"task_id": task.id, "status": db.PublishStatus.success.value}
    body = json.dumps(payload).encode()
    signature = hmac.new(b"secret", body, hashlib.sha256).hexdigest()

    client = TestClient(main.app)
    resp = client.post(
        f"/webhooks/{db.Marketplace.redbubble.value}",
        headers={"X-Signature": signature},
        json=payload,
    )
    assert resp.status_code == 200
