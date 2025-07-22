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


class RedisWithTTL(fakeredis.FakeRedis):
    """Fakeredis client with expiration support."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        kwargs["decode_responses"] = True
        super().__init__(*args, **kwargs)


@pytest.fixture()
def dedup_module(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[tuple[object, RedisWithTTL], None, None]:
    """Reload ``dedup`` with a fake redis client."""
    fake = RedisWithTTL()
    monkeypatch.setattr(cache, "get_sync_client", lambda: fake)
    sys.modules.pop("signal_ingestion.dedup", None)
    module = importlib.import_module("signal_ingestion.dedup")
    fake.delete(module.SET_KEY)
    yield module, fake


def test_initialize_creates_set_and_sets_ttl(
    dedup_module: tuple[object, RedisWithTTL],
) -> None:
    """``initialize`` creates set and sets TTL."""
    module, redis = dedup_module
    module.initialize(5)
    assert redis.exists(module.SET_KEY)
    ttl = redis.ttl(module.SET_KEY)
    assert 0 < ttl <= 5


def test_add_key_refreshes_ttl(dedup_module: tuple[object, RedisWithTTL]) -> None:
    """``add_key`` refreshes expiry on the set."""
    module, redis = dedup_module
    module.settings.dedup_ttl = 7
    module.initialize(3)
    redis.expire(module.SET_KEY, 1)
    module.add_key("foo")
    ttl = redis.ttl(module.SET_KEY)
    assert ttl > 1
    assert ttl <= module.settings.dedup_ttl


def test_is_duplicate(dedup_module: tuple[object, RedisWithTTL]) -> None:
    """``is_duplicate`` reports presence correctly."""
    module, _ = dedup_module
    module.initialize(5)
    assert not module.is_duplicate("foo")
    module.add_key("foo")
    assert module.is_duplicate("foo")
    assert not module.is_duplicate("bar")
