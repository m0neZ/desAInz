"""Wrapper for running ComfyUI workflows."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)


@dataclass
class ComfyResult:
    """Result information for a ComfyUI run."""

    image_path: str
    duration: float


class ComfyUIWorkflow:
    """Execute workflows on a running ComfyUI instance."""

    def __init__(self, base_url: str) -> None:
        """Store the base URL of the ComfyUI API."""
        self.base_url = base_url.rstrip("/")

    def execute(self, workflow: dict[str, Any], output_path: str) -> ComfyResult:
        """Send ``workflow`` to ComfyUI and wait for ``output_path``."""
        from time import perf_counter, sleep

        start = perf_counter()
        session = requests.Session()
        try:
            resp = session.post(f"{self.base_url}/prompt", json=workflow, timeout=30)
            resp.raise_for_status()
            for _ in range(30):
                if Path(output_path).exists():
                    break
                sleep(1)
            else:
                raise RuntimeError("ComfyUI did not produce output")
        except requests.RequestException as exc:  # pragma: no cover - network error
            raise RuntimeError("ComfyUI request failed") from exc
        duration = perf_counter() - start
        return ComfyResult(image_path=output_path, duration=duration)
