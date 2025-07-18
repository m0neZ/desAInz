"""Tests for trending keyword cache."""

from __future__ import annotations

import fakeredis

from signal_ingestion import trending
from backend.shared import cache
from backend.shared.config import settings


def test_store_keywords_sets_ttl(monkeypatch):
    """`store_keywords` refreshes TTL on the sorted set."""
    fake = fakeredis.FakeRedis()
    monkeypatch.setattr(cache, "get_sync_client", lambda: fake)
    trending.store_keywords(["foo", "bar"])
    ttl1 = fake.ttl(trending.TRENDING_KEY)
    assert 0 < ttl1 <= settings.trending_ttl
    trending.store_keywords(["foo"])
    ttl2 = fake.ttl(trending.TRENDING_KEY)
    assert ttl2 > 0
    assert ttl2 <= settings.trending_ttl
    assert ttl2 >= ttl1 - 1
