"""Tests for ``wait_for_services`` utilities."""

import socket
import time

import pytest

from importlib import import_module

wait_for_services = import_module("scripts.wait_for_services")


def test_wait_returns_quickly() -> None:
    """``_wait`` should exit promptly when service is ready."""

    with socket.socket() as server:
        server.bind(("localhost", 0))
        port = server.getsockname()[1]
        server.listen()

        start = time.monotonic()
        wait_for_services._wait("localhost", port, timeout=5)
        duration = time.monotonic() - start

    assert duration < 1


def test_wait_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sleep interval should double until the timeout is reached."""

    intervals: list[float] = []
    current = 0.0

    def fake_monotonic() -> float:
        return current

    def fake_sleep(seconds: float) -> None:
        nonlocal current
        intervals.append(seconds)
        current += seconds

    monkeypatch.setattr(wait_for_services.time, "monotonic", fake_monotonic)
    monkeypatch.setattr(wait_for_services.time, "sleep", fake_sleep)
    monkeypatch.setattr(
        wait_for_services.socket,
        "create_connection",
        lambda *a, **kw: (_ for _ in ()).throw(OSError),
    )

    with pytest.raises(TimeoutError):
        wait_for_services._wait("localhost", 1, timeout=3)

    assert intervals == [1, 2]
