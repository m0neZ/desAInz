"""Tests for the marketplace publisher API."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from _pytest.monkeypatch import MonkeyPatch
import anyio


def test_publish_and_progress(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    """Publish design and check initial progress."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    from marketplace_publisher.db import (
        Marketplace,
        PublishStatus,
        SessionLocal,
        create_task,
        init_db,
    )
    from marketplace_publisher import publisher, trademark

    class DummyClient:
        def publish_design(self, design_path: Path, metadata: dict[str, Any]) -> str:
            return "1"

    publisher.CLIENTS[Marketplace.redbubble] = DummyClient()
    publisher._fallback.publish = lambda *args, **kwargs: None
    called: list[str] = []

    async def dummy_check(term: str) -> None:
        called.append(term)

    monkeypatch.setattr(publisher, "verify_no_trademark_issue", dummy_check)

    design = tmp_path / "a.png"
    design.write_text("img")

    async def run() -> PublishStatus:
        await init_db()
        async with SessionLocal() as session:
            task = await create_task(
                session,
                marketplace=Marketplace.redbubble,
                design_path=str(design),
                metadata_json={"title": "t"},
            )
            await publisher.publish_with_retry(
                session,
                task.id,
                Marketplace.redbubble,
                design,
                {"title": "t"},
            )
            await session.refresh(task)
            return task.status

    status = anyio.run(run)

    assert called
    assert status == PublishStatus.success
