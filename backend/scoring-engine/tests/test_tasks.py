"""Tests for scoring engine Celery tasks."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from scoring_engine.tasks import batch_embed
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


def test_batch_embed_bulk_insertion(monkeypatch) -> None:
    """Embeddings are inserted using ``bulk_save_objects``."""

    monkeypatch.setattr(
        "signal_ingestion.embedding.generate_embedding", lambda *_: [0.0, 0.0]
    )
    captured: dict[str, list[Embedding] | None] = {"objs": None}

    def fake_bulk(self: Session, objs: list[Embedding], **_: object) -> None:
        captured["objs"] = list(objs)

    monkeypatch.setattr(Session, "bulk_save_objects", fake_bulk)
    signals = [{"id": i} for i in range(5)]
    batch_embed(signals)
    assert captured["objs"] is not None
    assert len(captured["objs"] or []) == 5
    assert isinstance((captured["objs"] or [])[0], Embedding)
