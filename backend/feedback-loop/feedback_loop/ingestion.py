"""Metric ingestion job."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterable, Mapping

import requests
from apscheduler.job import Job
from apscheduler.schedulers.base import BaseScheduler

import pandas as pd
from backend.shared.db import session_scope
from backend.shared.db import models

logger = logging.getLogger(__name__)


def ingest_metrics(metrics: Iterable[dict[str, float]]) -> pd.DataFrame:
    """Persist incoming metrics and return DataFrame."""
    df = pd.DataFrame(metrics)
    if "timestamp" not in df.columns:
        df["timestamp"] = datetime.now(timezone.utc)
    logger.info("ingested %s metrics", len(df))
    return df


def fetch_marketplace_metrics(
    api_url: str, listing_ids: Iterable[int]
) -> list[dict[str, float]]:
    """Fetch performance metrics for the given listings."""
    results: list[dict[str, float]] = []
    for listing_id in listing_ids:
        try:
            resp = requests.get(f"{api_url}/listings/{listing_id}/metrics", timeout=5)
            resp.raise_for_status()
            data = resp.json()
            results.append(
                {
                    "listing_id": float(listing_id),
                    "views": float(data.get("views", 0)),
                    "favorites": float(data.get("favorites", 0)),
                    "orders": float(data.get("orders", 0)),
                    "revenue": float(data.get("revenue", 0.0)),
                }
            )
        except requests.RequestException as exc:  # pragma: no cover - network
            logger.warning("failed to fetch metrics for %s: %s", listing_id, exc)
    return results


def store_marketplace_metrics(metrics: Iterable[Mapping[str, float]]) -> None:
    """Persist marketplace metrics to the database."""
    rows = [
        models.MarketplacePerformanceMetric(
            listing_id=int(m["listing_id"]),
            timestamp=datetime.now(timezone.utc),
            views=int(m["views"]),
            favorites=int(m["favorites"]),
            orders=int(m["orders"]),
            revenue=float(m["revenue"]),
        )
        for m in metrics
    ]
    if not rows:
        return
    with session_scope() as session:
        session.add_all(rows)
        logger.info("stored %s marketplace metrics", len(rows))


def schedule_marketplace_ingestion(
    scheduler: "BaseScheduler",
    api_url: str,
    listing_ids: Iterable[int],
    interval_minutes: int = 60,
) -> "Job":
    """Register a scheduled job to fetch and store marketplace metrics."""

    def _job() -> None:
        metrics = fetch_marketplace_metrics(api_url, listing_ids)
        store_marketplace_metrics(metrics)

    return scheduler.add_job(
        _job, "interval", minutes=interval_minutes, next_run_time=None
    )
