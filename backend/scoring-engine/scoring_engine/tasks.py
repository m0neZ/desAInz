"""Celery tasks for the scoring engine."""

from __future__ import annotations

import json
from typing import Mapping, cast

from celery import Task
from prometheus_client import Counter, Histogram

from backend.shared.db import session_scope
from backend.shared.db.models import Embedding
from signal_ingestion.embedding import generate_embedding, generate_embeddings

from .celery_app import app

BATCH_COUNTER = Counter("embed_batches_total", "Number of processed embedding batches")
SIGNAL_COUNTER = Counter(
    "embed_signals_total", "Number of signals processed for embeddings"
)
BATCH_SIZE_HISTOGRAM = Histogram(
    "embed_batch_size", "Number of signals per embedding batch"
)


@app.task(name="scoring_engine.tasks.batch_embed", bind=True)  # type: ignore[misc]
def batch_embed(self: Task, signals: list[Mapping[str, object]]) -> int:
    """Generate embeddings for ``signals`` and persist them."""
    BATCH_COUNTER.inc()
    BATCH_SIZE_HISTOGRAM.observe(len(signals))
    SIGNAL_COUNTER.inc(len(signals))

    with session_scope() as session:
        prepared: list[tuple[str, list[float] | None]] = []
        payloads: list[str] = []

        for msg in signals:
            embedding = msg.get("embedding")
            if embedding is None:
                payload = json.dumps(msg, default=str, sort_keys=True)
                payloads.append(payload)
                prepared.append((str(msg.get("source", "global")), None))
            else:
                prepared.append(
                    (
                        str(msg.get("source", "global")),
                        list(cast(list[float], embedding)),
                    )
                )

        computed = generate_embeddings(payloads)
        comp_idx = 0
        for source, emb in prepared:
            if emb is None:
                emb = computed[comp_idx]
                comp_idx += 1
            session.add(Embedding(source=source, embedding=emb))
        session.flush()
    return len(signals)
