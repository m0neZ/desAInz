"""Periodic job for computing embedding centroids."""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import func, select

from backend.shared.db import session_scope
from backend.shared.db.models import Embedding, Weights

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def compute_and_store_centroids() -> None:
    """Aggregate embeddings per source and store centroids."""
    with session_scope() as session:
        sources = session.scalars(select(Embedding.source).distinct()).all()
        for src in sources:
            centroid = session.execute(
                select(func.avg(Embedding.embedding)).where(Embedding.source == src)
            ).scalar_one()
            weights = session.scalar(select(Weights).where(Weights.source == src))
            if weights is None:
                weights = Weights(source=src)
                session.add(weights)
            weights.centroid = list(centroid)
        session.flush()
    logger.info("updated centroids for %s sources", len(sources))


def start_centroid_scheduler() -> None:
    """Start background scheduler for centroid updates."""
    scheduler.add_job(
        compute_and_store_centroids, "interval", hours=1, next_run_time=None
    )
    scheduler.start()
