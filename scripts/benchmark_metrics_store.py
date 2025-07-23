"""Benchmark MetricsStore with and without connection pooling."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from time import perf_counter

from backend.optimization.metrics import ResourceMetric
from backend.optimization.storage import MetricsStore

import sqlite3
import psycopg2


def benchmark_pooled(store: MetricsStore, runs: int) -> float:
    """Insert metrics using the pooled store."""
    metric = ResourceMetric(datetime.now(UTC), 50.0, 128.0, 256.0)
    start = perf_counter()
    for _ in range(runs):
        store.add_metric(metric)
    end = perf_counter()
    return end - start


def benchmark_unpooled(db_url: str, runs: int) -> float:
    """Insert metrics opening a new connection each time."""
    metric = ResourceMetric(datetime.now(UTC), 50.0, 128.0, 256.0)
    start = perf_counter()
    for _ in range(runs):
        if db_url.startswith("sqlite"):
            conn = sqlite3.connect(db_url.split("///", 1)[1])
            conn.execute(
                "INSERT INTO metrics VALUES (?, ?, ?, ?)",
                (
                    metric.timestamp.isoformat(),
                    metric.cpu_percent,
                    metric.memory_mb,
                    metric.disk_usage_mb,
                ),
            )
            conn.commit()
            conn.close()
        else:
            conn = psycopg2.connect(db_url)
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO metrics VALUES (%s, %s, %s, %s)",
                    (
                        metric.timestamp.isoformat(),
                        metric.cpu_percent,
                        metric.memory_mb,
                        metric.disk_usage_mb,
                    ),
                )
                conn.commit()
            conn.close()
    end = perf_counter()
    return end - start


def main(runs: int) -> None:
    """Execute pooled and unpooled benchmarks and print durations."""
    store = MetricsStore()
    unpooled = benchmark_unpooled(store.db_url, runs)
    pooled = benchmark_pooled(store, runs)
    print(f"Unpooled: {unpooled:.2f}s")
    print(f"Pooled:   {pooled:.2f}s")


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=100)
    args = parser.parse_args()
    main(args.runs)
