"""Ingestion orchestration."""

from __future__ import annotations


import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .adapters.events import EventsAdapter
from .adapters.instagram import InstagramAdapter
from .adapters.nostalgia import NostalgiaAdapter
from .adapters.reddit import RedditAdapter
from .adapters.tiktok import TikTokAdapter
from .adapters.youtube import YouTubeAdapter
from .dedup import add_key, is_duplicate
from .models import Signal
from .publisher import publish
from .database import SessionLocal
from .adapters.base import BaseAdapter


ADAPTERS = [
    TikTokAdapter("https://jsonplaceholder.typicode.com"),
    InstagramAdapter("https://jsonplaceholder.typicode.com"),
    RedditAdapter("https://jsonplaceholder.typicode.com"),
    YouTubeAdapter("https://jsonplaceholder.typicode.com"),
    EventsAdapter("https://jsonplaceholder.typicode.com"),
    NostalgiaAdapter("https://jsonplaceholder.typicode.com"),
]


async def _process_adapter(
    adapter: BaseAdapter, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """Fetch signals from a single adapter and persist them."""
    async with session_factory() as session:
        rows = await adapter.fetch()
        for row in rows:
            key = f"{adapter.__class__.__name__}:{row['id']}"
            if is_duplicate(key):
                continue
            add_key(key)
            signal = Signal(source=adapter.__class__.__name__, content=str(row))
            session.add(signal)
            await session.commit()
            publish("signals", key)


async def ingest(session: AsyncSession | None = None) -> None:
    """Fetch signals from adapters concurrently and store them."""
    await asyncio.gather(
        *(_process_adapter(adapter, SessionLocal) for adapter in ADAPTERS)
    )
