"""Celery tasks for mockup generation."""

from __future__ import annotations

from pathlib import Path
from contextlib import contextmanager
from typing import Iterator
import os
import time

import redis
from redis.lock import Lock as RedisLock

from PIL import Image
from .celery_app import app
from .generator import MockupGenerator
from .prompt_builder import PromptContext, build_prompt
from .post_processor import (
    compress_lossless,
    convert_to_cmyk,
    ensure_not_nsfw,
    remove_background,
    validate_color_space,
    validate_dpi_image,
)


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
GPU_SLOTS = int(os.getenv("GPU_SLOTS", "1"))
GPU_LOCK_TIMEOUT = int(os.getenv("GPU_LOCK_TIMEOUT", "600"))

redis_client = redis.Redis.from_url(REDIS_URL)

generator = MockupGenerator()


def _acquire_gpu_lock() -> RedisLock:
    """Acquire and return a lock for an available GPU slot."""
    while True:
        for idx in range(GPU_SLOTS):
            lock = redis_client.lock(
                f"gpu_slot:{idx}",
                timeout=GPU_LOCK_TIMEOUT,
                blocking_timeout=0,
            )
            if lock.acquire(blocking=False):
                return lock
        time.sleep(0.1)


@contextmanager
def gpu_slot() -> Iterator[None]:
    """Yield while holding a GPU slot lock."""
    lock = _acquire_gpu_lock()
    try:
        yield
    finally:
        lock.release()


@app.task  # type: ignore[misc]
def generate_mockup(keywords: list[str], output_dir: str) -> str:
    """Generate a mockup asynchronously."""
    context = PromptContext(keywords=keywords)
    prompt = build_prompt(context)
    output_path = Path(output_dir) / "mockup.png"
    with gpu_slot():
        result = generator.generate(prompt, str(output_path))

    processed = remove_background(Image.open(result.image_path))
    processed = convert_to_cmyk(processed)
    ensure_not_nsfw(processed)
    if not validate_dpi_image(processed):
        raise ValueError("Invalid DPI")
    if not validate_color_space(processed):
        raise ValueError("Invalid color space")
    compress_lossless(processed, output_path)
    return str(output_path)
