"""Ingestion orchestration."""

from __future__ import annotations


from sqlalchemy.ext.asyncio import AsyncSession

from .adapters.events import EventsAdapter
from .adapters.instagram import InstagramAdapter
from .adapters.nostalgia import NostalgiaAdapter
from .adapters.reddit import RedditAdapter
from .adapters.tiktok import TikTokAdapter
from .adapters.youtube import YouTubeAdapter
from .dedup import add_key, is_duplicate
from .models import Signal
from .publisher import publish


ADAPTERS = [
    TikTokAdapter("https://jsonplaceholder.typicode.com"),
    InstagramAdapter("https://jsonplaceholder.typicode.com"),
    RedditAdapter("https://jsonplaceholder.typicode.com"),
    YouTubeAdapter("https://jsonplaceholder.typicode.com"),
    EventsAdapter("https://jsonplaceholder.typicode.com"),
    NostalgiaAdapter("https://jsonplaceholder.typicode.com"),
]


async def ingest(session: AsyncSession) -> None:
    """Fetch signals from adapters and store them."""
    for adapter in ADAPTERS:
        rows = await adapter.fetch()
        signals = []
        for row in rows:
            key = f"{adapter.__class__.__name__}:{row['id']}"
            if is_duplicate(key):
                continue
            add_key(key)
            signals.append(Signal(source=adapter.__class__.__name__, content=str(row)))
            publish("signals", key)
        session.add_all(signals)
        await session.commit()
