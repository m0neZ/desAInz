"""Celery tasks for parallel signal ingestion."""

from __future__ import annotations

import asyncio
import json
from time import perf_counter
from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession
from prometheus_client import Counter, Histogram

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
from .models import Signal as DBSignal
from .embedding import generate_embeddings
from .privacy import purge_row
from .normalization import Signal as NormalizedSignal, normalize
from .publisher import publish
from .retention import purge_old_signals
from .settings import settings
from .trending import extract_keywords, store_keywords


EMBEDDING_CHUNK_SIZE = 16

_PROXIES = (
    [p or None for p in settings.http_proxies.split(",")]
    if settings.http_proxies
    else None
)
ADAPTERS: dict[str, BaseAdapter] = {
    "tiktok": TikTokAdapter(
        proxies=_PROXIES, rate_limit=settings.adapter_limit("tiktok")
    ),
    "instagram": InstagramAdapter(
        proxies=_PROXIES, rate_limit=settings.adapter_limit("instagram")
    ),
    "reddit": RedditAdapter(
        proxies=_PROXIES, rate_limit=settings.adapter_limit("reddit")
    ),
    "youtube": YouTubeAdapter(
        proxies=_PROXIES, rate_limit=settings.adapter_limit("youtube")
    ),
    "events": EventsAdapter(
        proxies=_PROXIES, rate_limit=settings.adapter_limit("events")
    ),
    "nostalgia": NostalgiaAdapter(
        proxies=_PROXIES, rate_limit=settings.adapter_limit("nostalgia")
    ),
}

# Task metrics
INGEST_DURATION = Histogram(
    "ingest_adapter_duration_seconds",
    "Time spent ingesting from adapter",
    ["adapter"],
)
INGEST_SUCCESS = Counter(
    "ingest_adapter_success_total",
    "Number of successful ingestions",
    ["adapter"],
)
INGEST_FAILURE = Counter(
    "ingest_adapter_failure_total",
    "Number of failed ingestions",
    ["adapter"],
)


async def _ingest_from_adapter(session: AsyncSession, adapter: BaseAdapter) -> None:
    """Ingest signals from ``adapter`` and persist them in batches."""
    await purge_old_signals(session, settings.signal_retention_days)
    rows: list[dict[str, object]] = await adapter.fetch()
    sanitized: list[tuple[str, str, NormalizedSignal]] = []
    for row in rows:
        signal_data = normalize(
            adapter.__class__.__name__.replace("Adapter", "").lower(), row
        )
        key = f"{adapter.__class__.__name__}:{signal_data.id}"
        if is_duplicate(key):
            continue
        add_key(key)
        clean_row = purge_row(signal_data.asdict())
        sanitized_json = json.dumps(clean_row)
        sanitized.append((key, sanitized_json, signal_data))

    for i in range(0, len(sanitized), EMBEDDING_CHUNK_SIZE):
        chunk = sanitized[i : i + EMBEDDING_CHUNK_SIZE]
        embeddings = generate_embeddings([text for _key, text, _data in chunk])
        for (key, sanitized_json, signal_data), embedding in zip(chunk, embeddings):
            signal = DBSignal(
                source=adapter.__class__.__name__,
                content=sanitized_json,
                embedding=embedding,
            )
            session.add(signal)
            await session.commit()
            publish("signals", key)
            publish("signals.ingested", sanitized_json)
            store_keywords(extract_keywords(signal_data.title))


@app.task(name="signal_ingestion.ingest_adapter")  # type: ignore[misc]
def ingest_adapter_task(adapter_name: str) -> None:
    """Run ingestion for the adapter named ``adapter_name``."""
    start = perf_counter()
    try:

        async def runner() -> None:
            adapter = ADAPTERS[adapter_name]
            async with SessionLocal() as session:
                await _ingest_from_adapter(session, adapter)

        asyncio.run(runner())
        INGEST_SUCCESS.labels(adapter_name).inc()
    except Exception:
        INGEST_FAILURE.labels(adapter_name).inc()
        raise
    finally:
        INGEST_DURATION.labels(adapter_name).observe(perf_counter() - start)


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
