"""Metric ingestion job."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Iterable, Mapping

import requests
from backend.shared.http import request_with_retry
import asyncio
from apscheduler.job import Job
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from marketplace_publisher.publisher import CLIENTS
from marketplace_publisher.clients import BaseClient
from sqlalchemy import func

from backend.shared.db import session_scope
from backend.shared.db import models
from scoring_engine import weight_repository
from .weight_updater import update_weights

logger = logging.getLogger(__name__)


def ingest_metrics(
    metrics: Iterable[Mapping[str, float | datetime]],
) -> list[dict[str, float | datetime]]:
    """Persist incoming metrics and return them with added timestamps."""

    metrics_list = [dict(m) for m in metrics]
    now = datetime.utcnow().replace(tzinfo=UTC)
    for entry in metrics_list:
        entry.setdefault("timestamp", now)
    logger.info("ingested %s metrics", len(metrics_list))
    return metrics_list


def fetch_marketplace_metrics(
    api_url: str, listing_ids: Iterable[int]
) -> list[dict[str, float]]:
    """Fetch performance metrics for the given listings."""
    results: list[dict[str, float]] = []
    for listing_id in listing_ids:
        try:
            resp = request_with_retry(
                "GET", f"{api_url}/listings/{listing_id}/metrics", timeout=5
            )
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
            timestamp=datetime.utcnow().replace(tzinfo=UTC),
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


async def _fetch_metrics_async(
    clients: Iterable["BaseClient"], listing_ids: Iterable[int]
) -> list[dict[str, float]]:
    async def _get(c: "BaseClient", lid: int) -> dict[str, float] | None:
        try:
            data = await asyncio.to_thread(c.get_listing_metrics, lid)
        except Exception as exc:  # pragma: no cover - network failures
            logger.warning(
                "failed to fetch metrics for %s from %s: %s", lid, c.base_url, exc
            )
            return None
        return {
            "listing_id": float(lid),
            "views": float(data.get("views", 0)),
            "favorites": float(data.get("favorites", 0)),
            "orders": float(data.get("orders", 0)),
            "revenue": float(data.get("revenue", 0.0)),
        }

    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(_get(c, lid)) for c in clients for lid in listing_ids]
    results = [t.result() for t in tasks]
    return [r for r in results if r]


def schedule_marketplace_ingestion(
    scheduler: "BaseScheduler",
    listing_ids: Iterable[int],
    scoring_api: str,
    interval_minutes: int = 60,
) -> Job:
    """Register a job fetching metrics and update scoring weights."""

    async def _job() -> None:
        metrics = await _fetch_metrics_async(list(CLIENTS.values()), listing_ids)
        store_marketplace_metrics(metrics)
        await asyncio.to_thread(update_weights_from_db, scoring_api)

    if isinstance(scheduler, AsyncIOScheduler):
        return scheduler.add_job(
            _job, "interval", minutes=interval_minutes, next_run_time=None
        )

    def _run_sync() -> None:
        asyncio.run(_job())

    return scheduler.add_job(
        _run_sync, "interval", minutes=interval_minutes, next_run_time=None
    )


def aggregate_marketplace_metrics() -> dict[str, float]:
    """Return aggregated marketplace metrics from the database."""
    with session_scope() as session:
        views, favorites, orders, revenue = session.query(
            func.coalesce(func.sum(models.MarketplacePerformanceMetric.views), 0),
            func.coalesce(func.sum(models.MarketplacePerformanceMetric.favorites), 0),
            func.coalesce(func.sum(models.MarketplacePerformanceMetric.orders), 0),
            func.coalesce(func.sum(models.MarketplacePerformanceMetric.revenue), 0.0),
        ).one()
    return {
        "views": float(views),
        "favorites": float(favorites),
        "orders": float(orders),
        "revenue": float(revenue),
    }


def update_weights_from_db(scoring_api: str) -> Mapping[str, float]:
    """Update scoring weights using aggregated marketplace metrics."""
    metrics = aggregate_marketplace_metrics()
    weights: Mapping[str, float] = update_weights(scoring_api, [metrics])
    weight_repository.update_weights(**weights)
    return weights
