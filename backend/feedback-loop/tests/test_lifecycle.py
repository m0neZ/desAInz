"""Lifecycle tests for startup and shutdown."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402
import feedback_loop.main as main  # noqa: E402


class DummyScheduler:
    """Capture start and shutdown calls."""

    def __init__(self) -> None:
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def shutdown(self) -> None:
        self.stopped = True


def test_scheduler_shutdown(monkeypatch) -> None:
    """Scheduler should be stopped on application shutdown."""
    dummy = DummyScheduler()

    def fake_setup_scheduler(*_: object, **__: object) -> DummyScheduler:
        return dummy

    import feedback_loop.scheduler as scheduler_mod

    monkeypatch.setattr(scheduler_mod, "setup_scheduler", fake_setup_scheduler)

    with TestClient(main.app) as client:
        assert dummy.started
        client.get("/health")
    assert dummy.stopped
