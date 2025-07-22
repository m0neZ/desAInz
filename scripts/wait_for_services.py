"""Block until required services respond on their ports."""

from __future__ import annotations

import os
import socket
import time

SERVICES = [
    ("postgres", 5432),
    ("redis", 6379),
    ("kafka", 9092),
    ("minio", 9000),
]


DEFAULT_TIMEOUT = int(os.getenv("WAIT_TIMEOUT", "30"))


def _wait(host: str, port: int, timeout: int = DEFAULT_TIMEOUT) -> None:
    """Wait for ``host``:``port`` to accept connections or raise ``TimeoutError``."""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            time.sleep(1)
    raise TimeoutError(f"Service {host}:{port} did not respond in {timeout} seconds")


def main() -> None:
    """Wait for all services to become available."""
    for host, port in SERVICES:
        print(f"Waiting for {host}:{port} ...")
        _wait(host, port)
        print(f"{host}:{port} is up")


if __name__ == "__main__":  # pragma: no cover
    main()
