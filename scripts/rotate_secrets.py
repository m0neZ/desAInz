#!/usr/bin/env python
"""Rotate service tokens and update Kubernetes secrets."""

from __future__ import annotations

import base64
import secrets
import subprocess
from typing import Iterable

SECRET_NAMES: list[str] = [
    "api-gateway",
    "marketplace-publisher",
    "scoring-engine",
]


def _generate_token(length: int = 32) -> str:
    """Return a secure random token."""
    return secrets.token_urlsafe(length)


def _kubectl_patch(secret_name: str, token: str) -> None:
    """Patch ``secret_name`` with the new ``token`` using ``kubectl``."""
    data = base64.b64encode(token.encode()).decode()
    subprocess.run(
        [
            "kubectl",
            "patch",
            "secret",
            secret_name,
            "--type=merge",
            "-p",
            f'{{"data": {{"SERVICE_TOKEN": "{data}"}}}}',
        ],
        check=True,
    )


def rotate(secrets_to_rotate: Iterable[str] | None = None) -> None:
    """Rotate the given secrets."""
    names = secrets_to_rotate or SECRET_NAMES
    for name in names:
        token = _generate_token()
        _kubectl_patch(f"{name}-secret", token)


def main() -> None:
    """Entry point for script execution."""
    rotate()


if __name__ == "__main__":  # pragma: no cover
    main()
