"""Celery tasks for the scoring engine."""

from __future__ import annotations

import orjson
from typing import Mapping, cast

from celery import Task
from prometheus_client import Counter, Histogram
from opentelemetry import trace

from backend.shared.db import session_scope
from backend.shared.db.models import Embedding
from signal_ingestion.embedding import generate_embedding

from .celery_app import app

tracer = trace.get_tracer(__name__)

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

    with tracer.start_as_current_span("batch_embed"):
        with session_scope() as session:
            objects: list[Embedding] = []
            for msg in signals:
                embedding = msg.get("embedding")
                if embedding is None:
                    payload = orjson.dumps(
                        msg,
                        option=orjson.OPT_SORT_KEYS,
                        default=str,
                    ).decode()
                    embedding_value = generate_embedding(payload)
                else:
                    embedding_value = list(cast(list[float], embedding))
                source = str(msg.get("source", "global"))
                objects.append(Embedding(source=source, embedding=embedding_value))
            session.bulk_save_objects(objects)
            session.flush()
        return len(signals)
