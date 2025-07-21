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


def _wait(host: str, port: int) -> None:
    while True:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            time.sleep(1)


def main() -> None:
    """Wait for all services to become available."""
    for host, port in SERVICES:
        print(f"Waiting for {host}:{port} ...")
        _wait(host, port)
        print(f"{host}:{port} is up")


if __name__ == "__main__":  # pragma: no cover
    main()
