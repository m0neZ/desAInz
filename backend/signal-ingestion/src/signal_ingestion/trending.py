"""Store and retrieve trending keywords in Redis."""

from __future__ import annotations

import re
from typing import Iterable
from typing import Pattern
import math
import time

import json
from typing import cast

from backend.shared.cache import get_sync_client
from backend.shared.cache import sync_get, sync_set
from backend.shared.config import settings

TRENDING_KEY = "trending:keywords"
TRENDING_TS_KEY = "trending:timestamps"
TRENDING_CACHE_PREFIX = "trending:list:"
_DECAY_BASE = math.e
_WORD_RE: Pattern[str] = re.compile(r"[A-Za-z0-9]+")


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


def get_trending(limit: int = 10) -> list[str]:
    """
    Return up to ``limit`` most popular keywords.

    Results are cached in Redis for a short period of time to avoid repeatedly scanning
    the sorted set on each request.
    """
    client = get_sync_client()
    cache_key = f"{TRENDING_CACHE_PREFIX}{limit}"
    cached = sync_get(cache_key, client)
    if cached:
        return cast(list[str], json.loads(cached))

    words = client.zrevrange(TRENDING_KEY, 0, limit - 1)
    result = [w.decode("utf-8") if isinstance(w, bytes) else w for w in words]
    sync_set(
        cache_key, json.dumps(result), ttl=settings.trending_cache_ttl, client=client
    )
    return result


def get_top_keywords(limit: int) -> list[str]:
    """Return the top ``limit`` keywords ordered by popularity."""
    return get_trending(limit)


def trim_keywords(max_size: int) -> None:
    """Decay scores, drop stale entries and limit sorted set size."""
    client = get_sync_client()
    now = int(time.time())
    cutoff = now - settings.trending_ttl
    stale_words = client.zrangebyscore(TRENDING_TS_KEY, 0, cutoff)
    pipe = client.pipeline()
    if stale_words:
        pipe.zrem(TRENDING_KEY, *stale_words)
    pipe.zremrangebyscore(TRENDING_TS_KEY, 0, cutoff)
    pipe.execute()
    pipe = client.pipeline()

    cursor = 0
    while True:
        cursor, words = client.zscan(TRENDING_KEY, cursor)
        for word, score in words:
            w = word.decode("utf-8") if isinstance(word, bytes) else word
            last_seen = client.zscore(TRENDING_TS_KEY, w)
            if last_seen is None:
                pipe.zrem(TRENDING_KEY, w)
                pipe.zrem(TRENDING_TS_KEY, w)
                continue
            elapsed = now - int(last_seen)
            decay = _DECAY_BASE ** (-elapsed / settings.trending_ttl)
            new_score = float(score) * decay
            if new_score <= 0:
                pipe.zrem(TRENDING_KEY, w)
                pipe.zrem(TRENDING_TS_KEY, w)
            else:
                pipe.zadd(TRENDING_KEY, {w: new_score})
        if cursor == 0:
            break
    pipe.execute()
    size = client.zcard(TRENDING_KEY)
    if size > max_size:
        excess = client.zrange(TRENDING_KEY, 0, size - max_size - 1)
        if excess:
            pipe = client.pipeline()
            pipe.zrem(TRENDING_KEY, *excess)
            pipe.zrem(TRENDING_TS_KEY, *excess)
            pipe.execute()
