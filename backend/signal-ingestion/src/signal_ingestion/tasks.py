"""Celery tasks for parallel signal ingestion."""

from __future__ import annotations

import asyncio
import json
from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from .adapters.base import BaseAdapter
from .adapters.events import EventsAdapter
from .adapters.instagram import InstagramAdapter
from .adapters.nostalgia import NostalgiaAdapter
from .adapters.reddit import RedditAdapter
from .adapters.tiktok import TikTokAdapter
from .adapters.youtube import YouTubeAdapter
from .celery_app import app
from .database import SessionLocal
from .dedup import add_key, is_duplicate
from .models import Signal
from .embedding import generate_embedding
from .privacy import purge_row
from .normalization import NormalizedSignal, normalize
from .publisher import publish
from .retention import purge_old_signals
from .settings import settings
from .trending import extract_keywords, store_keywords


ADAPTERS: dict[str, BaseAdapter] = {
    "tiktok": TikTokAdapter(),
    "instagram": InstagramAdapter(),
    "reddit": RedditAdapter(),
    "youtube": YouTubeAdapter(),
    "events": EventsAdapter(),
    "nostalgia": NostalgiaAdapter(),
}


async def _ingest_from_adapter(session: AsyncSession, adapter: BaseAdapter) -> None:
    await purge_old_signals(session, settings.signal_retention_days)
    rows = await adapter.fetch()
    for row in rows:
        signal_data: NormalizedSignal = normalize(
            adapter.__class__.__name__.replace("Adapter", "").lower(), row
        )
        key = f"{adapter.__class__.__name__}:{signal_data.id}"
        if is_duplicate(key):
            continue
        add_key(key)
        clean_row = purge_row(signal_data.asdict())
        signal = Signal(
            source=adapter.__class__.__name__,
            content=str(clean_row),
            embedding=generate_embedding(json.dumps(clean_row)),
        )
        session.add(signal)
        await session.commit()
        publish("signals", key)
        publish("signals.ingested", json.dumps(clean_row))
        store_keywords(extract_keywords(signal_data.title))


@app.task(name="signal_ingestion.ingest_adapter")  # type: ignore[misc]
def ingest_adapter_task(adapter_name: str) -> None:
    """Run ingestion for the adapter named ``adapter_name``."""

    async def runner() -> None:
        adapter = ADAPTERS[adapter_name]
        async with SessionLocal() as session:
            await _ingest_from_adapter(session, adapter)

    asyncio.run(runner())


def queue_for(adapter_name: str) -> str:
    """Return queue name for ``adapter_name``."""
    return f"ingestion_{adapter_name}"


def schedule_ingestion(adapter_names: Iterable[str]) -> None:
    """Dispatch ingestion tasks for ``adapter_names``."""
    for name in adapter_names:
        app.send_task(
            "signal_ingestion.ingest_adapter",
            args=[name],
            queue=queue_for(name),
        )
