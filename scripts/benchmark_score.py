#!/usr/bin/env python
"""
Benchmark scoring endpoint with and without Redis cache.

When executed with ``--persist`` the resulting durations are saved to the
``ScoreBenchmark`` table using :func:`backend.shared.db.session_scope`.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime
import os
from time import perf_counter

import httpx
from backend.shared.db import models, session_scope
from backend.shared.http import get_async_http_client


async def get_http_client() -> httpx.AsyncClient:
    """Return a shared HTTP client."""
    return await get_async_http_client()


async def _run(
    client: httpx.AsyncClient, url: str, payload: dict[str, object], runs: int
) -> float:
    start = perf_counter()
    for _ in range(runs):
        await client.post(url, json=payload)
    end = perf_counter()
    return end - start


async def main(persist: bool = False) -> tuple[float, float, int]:
    """
    Return uncached and cached benchmark durations.

    If ``persist`` is ``True`` the values are inserted into the
    :class:`backend.shared.db.models.ScoreBenchmark` table.
    """
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

    if persist:
        with session_scope() as session:
            session.add(
                models.ScoreBenchmark(
                    runs=runs,
                    uncached_seconds=uncached,
                    cached_seconds=cached,
                ),
            )

    return uncached, cached, runs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--persist",
        action="store_true",
        help="record results in the ScoreBenchmark table",
    )
    args = parser.parse_args()
    asyncio.run(main(persist=args.persist))
