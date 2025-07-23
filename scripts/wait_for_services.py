"""Block until required services respond on their ports."""

from __future__ import annotations

import argparse
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


def _wait(host: str, port: int, timeout: int = DEFAULT_TIMEOUT, max_interval: int = 5) -> None:
    """
    Wait for ``host``:``port`` to accept connections or raise ``TimeoutError``.

    Parameters
    ----------
    host:
        Hostname or IP of the service.
    port:
        Port number to connect to.
    timeout:
        Maximum number of seconds to wait.
    max_interval:
        Upper bound for the exponential backoff sleep interval.
    """

    end = time.monotonic() + timeout
    attempt = 0
    while time.monotonic() < end:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            sleep_seconds = min(2 ** attempt, max_interval)
            time.sleep(sleep_seconds)
            attempt += 1
    raise TimeoutError(f"Service {host}:{port} did not respond in {timeout} seconds")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Return command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-wait",
        type=int,
        default=DEFAULT_TIMEOUT,
        help="Maximum seconds to wait for each service.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Wait for all services to become available."""
    args = _parse_args(argv)
    for host, port in SERVICES:
        print(f"Waiting for {host}:{port} ...")
        _wait(host, port, timeout=args.max_wait)
        print(f"{host}:{port} is up")


if __name__ == "__main__":  # pragma: no cover
    main()
