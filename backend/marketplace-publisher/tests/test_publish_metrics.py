from __future__ import annotations

from pathlib import Path
import importlib

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from marketplace_publisher import db, main, publisher


@pytest.mark.asyncio()
async def test_metrics_stored_after_publish(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    async_url = f"sqlite+aiosqlite:///{tmp_path}/db.sqlite"
    sync_url = f"sqlite:///{tmp_path}/db.sqlite"

    engine = create_async_engine(async_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(db, "SessionLocal", session_factory)
    await db.init_db()

    monkeypatch.setenv("DATABASE_URL", sync_url)
    import backend.shared.db as shared_db

    importlib.reload(shared_db)
    from backend.shared.db import Base, models

    Base.metadata.create_all(shared_db.engine)

    class DummyClient:
        def publish_design(self, design_path: Path, metadata: dict[str, object]) -> str:
            return "1"

        def get_listing_metrics(self, listing_id: int) -> dict[str, float]:
            return {"views": 2, "favorites": 1, "orders": 1, "revenue": 4.0}

    publisher.CLIENTS[db.Marketplace.redbubble] = DummyClient()  # type: ignore[assignment]

    async with session_factory() as session:
        task = await db.create_task(
            session,
            marketplace=db.Marketplace.redbubble,
            design_path=str(tmp_path / "img.png"),
        )
        (tmp_path / "img.png").write_text("x")

    await main._background_publish(task.id)

    with shared_db.session_scope() as session:
        row = session.query(models.MarketplacePerformanceMetric).first()
        assert row is not None
        assert row.views == 2
        assert row.orders == 1

    Base.metadata.drop_all(shared_db.engine)
