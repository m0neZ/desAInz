from __future__ import annotations

import importlib
import os
import socket
from typing import Iterator

from celery.contrib.testing.worker import start_worker
import pytest


def _port_open(host: str, port: int) -> bool:
    s = socket.socket()
    try:
        s.settimeout(1)
        s.connect((host, port))
        return True
    except Exception:
        return False
    finally:
        s.close()


@pytest.mark.parametrize(
    "broker,url,port",
    [
        ("redis", "redis://localhost:6379/1", 6379),
        ("rabbitmq", "amqp://guest:guest@localhost:5672//", 5672),
    ],
)  # type: ignore[misc]
def test_worker_with_broker(monkeypatch: pytest.MonkeyPatch, broker: str, url: str, port: int) -> None:
    if not _port_open("localhost", port):
        pytest.skip(f"{broker} not available")

    os.environ["CELERY_BROKER"] = broker
    os.environ["CELERY_BROKER_URL"] = url
    os.environ["CELERY_RESULT_BACKEND"] = url

    import mockup_generation.celery_app as celery_app
    importlib.reload(celery_app)

    app = celery_app.app

    @app.task  # type: ignore[misc]
    def add(x: int, y: int) -> int:
        return x + y

    with start_worker(app, perform_ping_check=False, pool="solo"):
        res = add.delay(1, 2)
        assert res.get(timeout=10) == 3
