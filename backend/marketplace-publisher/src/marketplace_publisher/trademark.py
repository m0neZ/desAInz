"""Trademark check utilities using USPTO and EUIPO APIs."""

from __future__ import annotations

import httpx


class TrademarkError(Exception):
    """Raised when a trademark violation is detected."""


async def check_uspto(term: str) -> bool:
    """Return ``True`` if the term exists in USPTO records."""
    url = "https://developer.uspto.gov/ibd-api/v1/application/publications"
    params = {"searchText": term}
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    return bool(data.get("results"))


async def check_euipo(term: str) -> bool:
    """Return ``True`` if the term exists in EUIPO records."""
    url = "https://www.tmdn.org/tmview/api/rest/v1/search"
    params = {"query": term}
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    return bool(data.get("results"))


async def verify_no_trademark_issue(term: str) -> None:
    """Raise :class:`TrademarkError` if the term is trademarked."""
    if not term:
        return
    uspto, euipo = await check_uspto(term), await check_euipo(term)
    if uspto or euipo:
        raise TrademarkError(f"'{term}' may infringe on an existing trademark")
