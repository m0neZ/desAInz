#!/usr/bin/env python
"""Benchmark scoring endpoint with and without Redis cache."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import os
from time import perf_counter

import httpx
import atexit

_HTTP_CLIENT: httpx.AsyncClient | None = None


async def get_http_client() -> httpx.AsyncClient:
    """Return a shared HTTP client."""
    global _HTTP_CLIENT
    if _HTTP_CLIENT is None:
        _HTTP_CLIENT = httpx.AsyncClient()
    return _HTTP_CLIENT


@atexit.register
def _close_http_client() -> None:
    if _HTTP_CLIENT is not None:
        asyncio.run(_HTTP_CLIENT.aclose())


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
        "timestamp": datetime.utcnow().replace(tzinfo=UTC).isoformat(),
        "engagement_rate": 1.0,
        "embedding": [0.1, 0.2],
    }
    client = await get_http_client()
    # Warm up
    await client.post(url, json=payload)
    uncached = await _run(client, url, payload, runs)
    cached = await _run(client, url, payload, runs)
    print(f"Uncached: {uncached:.2f}s for {runs} runs")
    print(f"Cached:   {cached:.2f}s for {runs} runs")
    return uncached, cached, runs


if __name__ == "__main__":
    asyncio.run(main())
