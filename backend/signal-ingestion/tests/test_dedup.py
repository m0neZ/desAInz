"""Tests for deduplication bloom filter."""

from __future__ import annotations

import importlib
import os
import sys
from typing import Generator

import fakeredis
import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from backend.shared import cache


class FakeBloom:
    """Minimal bloom filter simulation."""

    def __init__(self, redis: fakeredis.FakeRedis) -> None:
        self.redis = redis
        self.items: set[str] = set()

    def create(self, key: str, error_rate: float, capacity: int) -> None:
        self.redis.set(key, "1")

    def add(self, key: str, item: str) -> None:
        self.items.add(item)

    def exists(self, key: str, item: str) -> int:
        return int(item in self.items)


class RedisWithBloom(fakeredis.FakeRedis):
    """FakeRedis with bloom filter support."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        kwargs["decode_responses"] = True
        super().__init__(*args, **kwargs)
        self._bloom = FakeBloom(self)

    def bf(self) -> FakeBloom:
        return self._bloom


@pytest.fixture()
def dedup_module(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[tuple[object, RedisWithBloom], None, None]:
    """Reload ``dedup`` with a fake redis client."""
    fake = RedisWithBloom()
    monkeypatch.setattr(cache, "get_sync_client", lambda: fake)
    sys.modules.pop("signal_ingestion.dedup", None)
    module = importlib.import_module("signal_ingestion.dedup")
    fake.delete(module.BLOOM_KEY)
    yield module, fake


def test_initialize_creates_bloom_and_sets_ttl(
    dedup_module: tuple[object, RedisWithBloom],
) -> None:
    """``initialize`` creates bloom filter and sets TTL."""
    module, redis = dedup_module
    module.initialize(0.1, 10, 5)
    assert redis.exists(module.BLOOM_KEY)
    ttl = redis.ttl(module.BLOOM_KEY)
    assert 0 < ttl <= 5


def test_add_key_refreshes_ttl(dedup_module: tuple[object, RedisWithBloom]) -> None:
    """``add_key`` refreshes expiry on the bloom filter."""
    module, redis = dedup_module
    module.settings.dedup_ttl = 7
    module.initialize(0.1, 10, 3)
    redis.expire(module.BLOOM_KEY, 1)
    module.add_key("foo")
    ttl = redis.ttl(module.BLOOM_KEY)
    assert ttl > 1
    assert ttl <= module.settings.dedup_ttl


def test_is_duplicate(dedup_module: tuple[object, RedisWithBloom]) -> None:
    """``is_duplicate`` reports presence correctly."""
    module, _ = dedup_module
    module.initialize(0.1, 10, 5)
    assert not module.is_duplicate("foo")
    module.add_key("foo")
    assert module.is_duplicate("foo")
    assert not module.is_duplicate("bar")
