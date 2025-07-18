"""Store and retrieve trending keywords in Redis."""

from __future__ import annotations

import re
from typing import Iterable

from backend.shared.cache import get_sync_client
from backend.shared.config import settings

TRENDING_KEY = "trending:keywords"
_WORD_RE = re.compile(r"[A-Za-z0-9]+")


def extract_keywords(text: str | None) -> list[str]:
    """Return lowercase tokens extracted from ``text``."""
    if not text:
        return []
    return [m.group(0).lower() for m in _WORD_RE.finditer(text)]


def store_keywords(keywords: Iterable[str]) -> None:
    """Increment counts for ``keywords`` and refresh TTL."""
    client = get_sync_client()
    pipe = client.pipeline()
    for word in keywords:
        pipe.zincrby(TRENDING_KEY, 1, word)
    pipe.expire(TRENDING_KEY, settings.trending_ttl)
    pipe.execute()
