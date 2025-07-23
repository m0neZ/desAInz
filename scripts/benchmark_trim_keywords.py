"""Benchmark trim_keywords performance with a large sorted set."""

from __future__ import annotations

import argparse
import time
from time import perf_counter

import fakeredis

from signal_ingestion import trending


def main(size: int) -> float:
    """Populate ``size`` keywords and measure ``trim_keywords`` duration."""
    fake = fakeredis.FakeRedis()
    trending.get_sync_client = lambda: fake
    now = int(time.time())
    for i in range(size):
        word = f"word{i}"
        fake.zadd(trending.TRENDING_KEY, {word: float(i)})
        fake.zadd(trending.TRENDING_TS_KEY, {word: now})
    start = perf_counter()
    trending.trim_keywords(size)
    end = perf_counter()
    duration = end - start
    print(f"Trimmed {size} keywords in {duration:.2f}s")
    return duration


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=100000)
    args = parser.parse_args()
    main(args.size)
