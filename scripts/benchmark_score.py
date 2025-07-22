#!/usr/bin/env python
"""Benchmark scoring endpoint with and without Redis cache."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import os
from time import perf_counter

import httpx
import atexit
import asyncio

_ASYNC_CLIENT: httpx.AsyncClient | None = None


async def get_async_client() -> httpx.AsyncClient:
    """Return a shared ``AsyncClient`` instance."""
    global _ASYNC_CLIENT
    if _ASYNC_CLIENT is None:
        _ASYNC_CLIENT = httpx.AsyncClient()
    return _ASYNC_CLIENT


@atexit.register
def _close_client() -> None:
    if _ASYNC_CLIENT is not None:
        asyncio.run(_ASYNC_CLIENT.aclose())


async def _run(
    client: httpx.AsyncClient, url: str, payload: dict[str, object], runs: int
) -> float:
    start = perf_counter()
    for _ in range(runs):
        await client.post(url, json=payload)
    end = perf_counter()
    return end - start


async def main() -> tuple[float, float, int]:
    """Return uncached and cached benchmark durations."""
    url = os.environ.get("SCORING_URL", "http://localhost:5002/score")
    runs = int(os.environ.get("RUNS", "100"))
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engagement_rate": 1.0,
        "embedding": [0.1, 0.2],
    }
    client = await get_async_client()
    # Warm up
    await client.post(url, json=payload)
    uncached = await _run(client, url, payload, runs)
    cached = await _run(client, url, payload, runs)
    print(f"Uncached: {uncached:.2f}s for {runs} runs")
    print(f"Cached:   {cached:.2f}s for {runs} runs")
    return uncached, cached, runs


if __name__ == "__main__":
    asyncio.run(main())
