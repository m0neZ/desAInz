"""Utilities for normalizing adapter payloads."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict


@dataclass
class NormalizedSignal:
    """Standard representation of an ingested signal."""

    id: str
    title: str | None
    url: str | None
    source: str

    def asdict(self) -> Dict[str, Any]:
        """Return the signal as a plain dictionary."""
        return asdict(self)


def _extract_between(text: str | None, start: str, end: str) -> str:
    """Return substring of ``text`` between ``start`` and ``end`` if present."""
    if not text:
        return ""
    s = text.find(start)
    if s == -1:
        return ""
    s += len(start)
    e = text.find(end, s)
    return text[s:e] if e != -1 else text[s:]


def normalize_tiktok(data: Dict[str, Any]) -> NormalizedSignal:
    """Normalize TikTok API response into a :class:`NormalizedSignal`."""
    video_id = data.get("embed_product_id") or _extract_between(
        data.get("html"), 'data-video-id="', '"'
    )
    return NormalizedSignal(
        id=str(video_id),
        title=data.get("title"),
        url=data.get("author_url"),
        source="tiktok",
    )


def normalize_instagram(data: Dict[str, Any]) -> NormalizedSignal:
    """Normalize Instagram data into a :class:`NormalizedSignal`."""
    return NormalizedSignal(
        id=str(data.get("id", "")),
        title=data.get("caption") or data.get("title") or data.get("author_name"),
        url=data.get("permalink") or data.get("author_url"),
        source="instagram",
    )


def normalize_reddit(data: Dict[str, Any]) -> NormalizedSignal:
    """Normalize Reddit data into a :class:`NormalizedSignal`."""
    if "data" in data:
        post = data["data"]["children"][0]["data"]
        post_id = post["id"]
        title = post["title"]
        url = f"https://www.reddit.com{post['permalink']}"
    else:
        post_id = str(data.get("id", ""))
        title = data.get("title")
        url = None
    return NormalizedSignal(id=post_id, title=title, url=url, source="reddit")


def normalize_youtube(data: Dict[str, Any]) -> NormalizedSignal:
    """Normalize YouTube data into a :class:`NormalizedSignal`."""
    video_id = _extract_between(data.get("html"), "embed/", "?")
    return NormalizedSignal(
        id=video_id,
        title=data.get("title"),
        url=data.get("url"),
        source="youtube",
    )


def normalize_events(data: Dict[str, Any]) -> NormalizedSignal:
    """Normalize event data into a :class:`NormalizedSignal`."""
    return NormalizedSignal(
        id=data["date"],
        title=data["name"],
        url=None,
        source="events",
    )


def normalize_nostalgia(data: Dict[str, Any]) -> NormalizedSignal:
    """Normalize Internet Archive data into a :class:`NormalizedSignal`."""
    doc = data["response"]["docs"][0]
    identifier = doc.get("identifier", "")
    return NormalizedSignal(
        id=identifier,
        title=doc.get("title"),
        url=f"https://archive.org/details/{identifier}" if identifier else None,
        source="nostalgia",
    )


NORMALIZERS: Dict[str, Callable[[Dict[str, Any]], NormalizedSignal]] = {
    "tiktok": normalize_tiktok,
    "instagram": normalize_instagram,
    "reddit": normalize_reddit,
    "youtube": normalize_youtube,
    "events": normalize_events,
    "nostalgia": normalize_nostalgia,
}


def normalize(source: str, data: Dict[str, Any]) -> NormalizedSignal:
    """Normalize ``data`` from ``source`` into a :class:`NormalizedSignal`."""
    if source not in NORMALIZERS:
        raise ValueError(f"Unknown source: {source}")
    return NORMALIZERS[source](data)
