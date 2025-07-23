"""Store and retrieve trending keywords in Redis."""

from __future__ import annotations

from typing import Iterable, Pattern, cast

import json
import math
import time

from backend.shared.regex_utils import compile_cached

from backend.shared.cache import get_sync_client
from backend.shared.cache import sync_get, sync_set
from backend.shared.config import settings

TRENDING_KEY = "trending:keywords"
TRENDING_TS_KEY = "trending:timestamps"
TRENDING_CACHE_PREFIX = "trending:list:"
_DECAY_BASE = math.e
_WORD_RE: Pattern[str] = compile_cached(r"\w+")


def extract_keywords(text: str | None) -> list[str]:
    """Return lowercase tokens extracted from ``text``."""
    if not text:
        return []
    return [m.group(0).lower() for m in _WORD_RE.finditer(text)]


def store_keywords(keywords: Iterable[str]) -> None:
    """Increment counts for ``keywords`` and refresh TTL."""
    client = get_sync_client()
    pipe = client.pipeline()
    now = int(time.time())
    for word in keywords:
        pipe.zincrby(TRENDING_KEY, 1, word)
        pipe.zadd(TRENDING_TS_KEY, {word: now})
    pipe.expire(TRENDING_KEY, settings.trending_ttl)
    pipe.expire(TRENDING_TS_KEY, settings.trending_ttl)
    pipe.execute()


def get_trending(limit: int = 10, offset: int = 0) -> list[str]:
    """
    Return ``limit`` popular keywords starting from ``offset``.

    Results are cached in Redis for a short period of time to avoid repeatedly scanning
    the sorted set on each request.
    """
    client = get_sync_client()
    cache_key = f"{TRENDING_CACHE_PREFIX}{limit}:{offset}"
    cached = sync_get(cache_key, client)
    if cached:
        return cast(list[str], json.loads(cached))

    words = client.zrevrange(TRENDING_KEY, offset, offset + limit - 1)
    result = [w.decode("utf-8") if isinstance(w, bytes) else w for w in words]
    sync_set(
        cache_key, json.dumps(result), ttl=settings.trending_cache_ttl, client=client
    )
    return result


def get_top_keywords(limit: int, offset: int = 0) -> list[str]:
    """Return ``limit`` keywords ordered by popularity starting from ``offset``."""
    return get_trending(limit, offset)


def trim_keywords(max_size: int) -> None:
    """Decay scores, drop stale entries and limit sorted set size."""
    client = get_sync_client()
    now = int(time.time())
    step_decay = _DECAY_BASE ** (-1 / settings.trending_ttl)
    cutoff = now - settings.trending_ttl
    stale_words = client.zrangebyscore(TRENDING_TS_KEY, 0, cutoff)
    pipe = client.pipeline()
    if stale_words:
        pipe.zrem(TRENDING_KEY, *stale_words)
    pipe.zremrangebyscore(TRENDING_TS_KEY, 0, cutoff)
    pipe.execute()

    def _process(words: list[tuple[str, float]]) -> None:
        ts_pipe = client.pipeline()
        for w, _ in words:
            ts_pipe.zscore(TRENDING_TS_KEY, w)
        timestamps = ts_pipe.execute()

        update_pipe = client.pipeline()
        for (w, score), last_seen in zip(words, timestamps):
            if last_seen is None:
                update_pipe.zrem(TRENDING_KEY, w)
                update_pipe.zrem(TRENDING_TS_KEY, w)
                continue
            elapsed = now - int(last_seen)
            decay = step_decay**elapsed
            new_score = float(score) * decay
            if new_score <= 0:
                update_pipe.zrem(TRENDING_KEY, w)
                update_pipe.zrem(TRENDING_TS_KEY, w)
            else:
                update_pipe.zadd(TRENDING_KEY, {w: new_score})
        update_pipe.execute()

    batch: list[tuple[str, float]] = []
    for word, score in client.zscan_iter(TRENDING_KEY, count=1000):
        w = word.decode("utf-8") if isinstance(word, bytes) else word
        batch.append((w, float(score)))
        if len(batch) >= 1000:
            _process(batch)
            batch.clear()
    if batch:
        _process(batch)

    size = client.zcard(TRENDING_KEY)
    if size > max_size:
        excess = client.zrange(TRENDING_KEY, 0, size - max_size - 1)
        if excess:
            pipe = client.pipeline()
            pipe.zrem(TRENDING_KEY, *excess)
            pipe.zrem(TRENDING_TS_KEY, *excess)
            pipe.execute()
