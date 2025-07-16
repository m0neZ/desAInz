"""Adapter tests with VCR recordings."""

from __future__ import annotations

import os
import sys
import pytest
import vcr

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from signal_ingestion.adapters.events import EventsAdapter  # noqa: E402
from signal_ingestion.adapters.instagram import InstagramAdapter  # noqa: E402
from signal_ingestion.adapters.nostalgia import NostalgiaAdapter  # noqa: E402
from signal_ingestion.adapters.reddit import RedditAdapter  # noqa: E402
from signal_ingestion.adapters.tiktok import TikTokAdapter  # noqa: E402
from signal_ingestion.adapters.youtube import YouTubeAdapter  # noqa: E402

ADAPTERS = [
    (TikTokAdapter, "tiktok"),
    (InstagramAdapter, "instagram"),
    (RedditAdapter, "reddit"),
    (YouTubeAdapter, "youtube"),
    (EventsAdapter, "events"),
    (NostalgiaAdapter, "nostalgia"),
]


@pytest.mark.parametrize("adapter_cls, name", ADAPTERS)
@pytest.mark.asyncio()
async def test_fetch(adapter_cls, name) -> None:
    """Each adapter should fetch one item."""
    adapter = adapter_cls("https://jsonplaceholder.typicode.com")
    cassette = f"backend/signal-ingestion/tests/cassettes/{name}.yaml"
    with vcr.use_cassette(cassette):
        rows = await adapter.fetch()
    assert len(rows) == 1
    assert "id" in rows[0]
