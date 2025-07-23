"""Wrapper for running ComfyUI workflows."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import asyncio
import httpx

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ComfyResult:
    """Result information for a ComfyUI run."""

    image_path: str
    duration: float


class ComfyUIWorkflow:
    """Execute workflows on a running ComfyUI instance."""

    def __init__(self, base_url: str) -> None:
        """Store the base URL of the ComfyUI API."""
        self.base_url = base_url.rstrip("/")

    async def execute(self, workflow: dict[str, Any], output_path: str) -> ComfyResult:
        """Send ``workflow`` to ComfyUI and wait for ``output_path``."""
        from time import perf_counter

        start = perf_counter()
        try:
            async with httpx.AsyncClient(timeout=30) as session:
                resp = await session.post(f"{self.base_url}/prompt", json=workflow)
                resp.raise_for_status()
                for _ in range(30):
                    if Path(output_path).exists():
                        break
                    await asyncio.sleep(1)
                else:
                    raise RuntimeError("ComfyUI did not produce output")
        except httpx.HTTPError as exc:  # pragma: no cover - network error
            raise RuntimeError("ComfyUI request failed") from exc
        duration = perf_counter() - start
        return ComfyResult(image_path=output_path, duration=duration)
