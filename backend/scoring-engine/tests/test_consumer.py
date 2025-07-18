"""Tests for the Kafka consumer used by the scoring engine."""

# mypy: ignore-errors

from __future__ import annotations

from threading import Event
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from sqlalchemy import select

from scoring_engine.app import consume_signals
from backend.shared.db import session_scope
from backend.shared.db.models import Embedding


class DummyConsumer:
    """Yield predetermined Kafka messages."""

    def __init__(self, messages: list[tuple[str, dict[str, object]]]) -> None:
        self._messages = messages

    def __iter__(self) -> object:
        """Return iterator over stored messages."""
        return iter(self._messages)


def test_consume_signals_stores_embeddings() -> None:
    """Store embeddings from Kafka messages into the database."""
    embedding = [0.0] * 768
    embedding[0] = 1.0
    consumer = DummyConsumer(
        [("signals.ingested", {"embedding": embedding, "source": "src"})]
    )
    stop = Event()
    consume_signals(stop, consumer)
    with session_scope() as session:
        row = session.scalar(select(Embedding))
        assert row is not None
        assert row.source == "src"
        assert row.embedding[0] == 1.0
