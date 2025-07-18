"""Tests for signal normalization."""

from __future__ import annotations

import os
import sys
from typing import Type

import httpx
import pytest
import vcr

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from signal_ingestion.adapters.tiktok import TikTokAdapter
from signal_ingestion.adapters.instagram import InstagramAdapter
from signal_ingestion.adapters.reddit import RedditAdapter
from signal_ingestion.adapters.youtube import YouTubeAdapter
from signal_ingestion.adapters.events import EventsAdapter
from signal_ingestion.adapters.nostalgia import NostalgiaAdapter
from signal_ingestion.normalization import normalize

ADAPTERS: list[tuple[Type[object], str]] = [
    (TikTokAdapter, "tiktok"),
    (RedditAdapter, "reddit"),
    (YouTubeAdapter, "youtube"),
    (EventsAdapter, "events"),
    (NostalgiaAdapter, "nostalgia"),
]


@pytest.mark.parametrize("adapter_cls, name", ADAPTERS)
@pytest.mark.asyncio()
async def test_normalize_success(adapter_cls: Type[object], name: str) -> None:
    """Adapter fetch results can be normalized."""
    adapter = adapter_cls()
    cassette = f"backend/signal-ingestion/tests/cassettes/{name}_real.yaml"
    with vcr.use_cassette(cassette, record_mode="new_episodes"):
        rows = await adapter.fetch()
    sig = normalize(name, rows[0])
    assert sig.id
    assert sig.source == name


@pytest.mark.asyncio()
async def test_fetch_error() -> None:
    """HTTP errors are surfaced as exceptions."""
    adapter = TikTokAdapter(base_url="https://example.com/doesnotexist")
    with pytest.raises(httpx.HTTPStatusError):
        await adapter.fetch()
