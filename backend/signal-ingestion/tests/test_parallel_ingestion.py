"""Test scheduling of ingestion tasks across queues."""

from __future__ import annotations

from signal_ingestion import tasks


class DummyApp:
    """Collect Celery send_task calls."""

    def __init__(self) -> None:
        """Initialize storage for sent tasks."""
        self.sent: list[tuple[str, list[str], str | None]] = []

    def send_task(
        self, name: str, args: list[str] | None = None, queue: str | None = None
    ) -> None:
        """Record a send_task call."""
        self.sent.append((name, args or [], queue))


def test_schedule_ingestion(monkeypatch) -> None:
    """Ensure each adapter is dispatched to its own queue."""
    dummy = DummyApp()
    monkeypatch.setattr(tasks, "app", dummy)
    tasks.schedule_ingestion(["tiktok", "instagram"])
    assert dummy.sent == [
        ("signal_ingestion.ingest_adapter", ["tiktok"], tasks.queue_for("tiktok")),
        (
            "signal_ingestion.ingest_adapter",
            ["instagram"],
            tasks.queue_for("instagram"),
        ),
    ]
