"""Background scheduler for computing embedding centroids."""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
from datetime import datetime
import numpy as np

from backend.shared.db import session_scope
from backend.shared.db.models import Embedding, Weights

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def compute_and_store_centroids() -> None:
    """Aggregate embeddings per source and store centroids."""
    with session_scope() as session:
        sources = session.scalars(select(Embedding.source).distinct()).all()
        for src in sources:
            vectors = session.scalars(
                select(Embedding.embedding).where(Embedding.source == src)
            ).all()
            if not vectors:
                continue
            arr = np.array(vectors, dtype=float)
            centroid = arr.mean(axis=0).tolist()
            weights = session.scalar(select(Weights).where(Weights.source == src))
            if weights is None:
                weights = Weights(source=src)
                session.add(weights)
            weights.centroid = centroid
        session.flush()
    logger.info("updated centroids for %s sources", len(sources))


def start_centroid_scheduler() -> None:
    """Start background scheduler for centroid updates."""
    scheduler.add_job(
        compute_and_store_centroids,
        trigger=IntervalTrigger(hours=1, start_date=datetime.utcnow()),
    )
    scheduler.start()
