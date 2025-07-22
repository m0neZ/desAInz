"""Collect resource usage metrics from services and forward them."""

from __future__ import annotations

import argparse
import logging
import tracemalloc
from datetime import UTC, datetime
from typing import Iterable

import requests

logger = logging.getLogger(__name__)


def fetch_overview(url: str) -> dict[str, float]:
    """Return overview metrics from a service."""
    resp = requests.get(f"{url}/overview", timeout=5)
    resp.raise_for_status()
    data = resp.json()
    return {
        "cpu_percent": float(data.get("cpu_percent", 0.0)),
        "memory_mb": float(data.get("memory_mb", 0.0)),
    }


def submit_metric(opt_url: str, metric: dict[str, float]) -> None:
    """Send a metric to the optimization service."""
    payload = {
        "timestamp": datetime.utcnow().replace(tzinfo=UTC).isoformat(),
        "cpu_percent": metric["cpu_percent"],
        "memory_mb": metric["memory_mb"],
    }
    requests.post(f"{opt_url}/metrics", json=payload, timeout=5)


def collect(service_urls: Iterable[str], opt_url: str) -> None:
    """Collect metrics from each service and forward them."""
    for url in service_urls:
        metric = fetch_overview(url)
        submit_metric(opt_url, metric)


def main() -> None:
    """Entry point for the metrics collection script."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("services", nargs="+", help="Service base URLs")
    parser.add_argument(
        "--optimization-url",
        default="http://localhost:5007",
        help="Optimization service base URL",
    )
    args = parser.parse_args()
    tracemalloc.start()
    try:
        collect(args.services, args.optimization_url)
    finally:
        current, peak = tracemalloc.get_traced_memory()
        logger.info(
            "Current memory usage: %.1f KiB; Peak: %.1f KiB",
            current / 1024,
            peak / 1024,
        )
        tracemalloc.stop()


if __name__ == "__main__":  # pragma: no cover
    main()
