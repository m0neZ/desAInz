"""Tests for scoring engine Celery tasks."""

from __future__ import annotations

from scoring_engine.tasks import batch_embed
from sqlalchemy import select

from backend.shared.db import session_scope
from backend.shared.db.models import Embedding


def test_batch_embed_persists_embeddings(monkeypatch) -> None:
    """Embeddings are generated and stored for each signal."""

    monkeypatch.setattr(
        "signal_ingestion.embedding.generate_embedding", lambda *_: [1.0, 0.0]
    )
    signals = [{"id": 1, "source": "s"}]
    batch_embed(signals)
    with session_scope() as session:
        row = session.scalar(select(Embedding))
        assert row is not None
        assert row.source == "s"
        assert row.embedding[0] == 1.0
