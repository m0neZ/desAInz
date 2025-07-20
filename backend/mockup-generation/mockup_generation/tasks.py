"""Celery tasks for mockup generation."""

from __future__ import annotations

from pathlib import Path
from contextlib import contextmanager
from typing import Iterator
import os
import time

import redis
from redis.lock import Lock as RedisLock
from celery import Task
from prometheus_client import Counter, Gauge

from PIL import Image
from .celery_app import app
from .generator import MockupGenerator
from .prompt_builder import PromptContext, build_prompt
from .listing_generator import ListingGenerator
from .post_processor import (
    compress_lossless,
    convert_to_cmyk,
    ensure_not_nsfw,
    remove_background,
    validate_color_space,
    validate_dpi_image,
)
from backend.shared.config import settings
from . import model_repository


def _get_storage_client():
    """Return a MinIO or boto3 client based on environment configuration."""
    if settings.s3_endpoint and "amazonaws" not in settings.s3_endpoint:
        from minio import Minio  # type: ignore

        secure = settings.s3_endpoint.startswith("https")
        host = settings.s3_endpoint.replace("https://", "").replace("http://", "")
        return Minio(
            host,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            secure=secure,
        )
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
    )


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DEFAULT_GPU_SLOTS = int(os.getenv("GPU_SLOTS", "1"))
GPU_LOCK_TIMEOUT = int(os.getenv("GPU_LOCK_TIMEOUT", "600"))
GPU_QUEUE_PREFIX = os.getenv("GPU_QUEUE_PREFIX", "gpu")
GPU_WORKER_INDEX = int(os.getenv("GPU_WORKER_INDEX", "-1"))

redis_client = redis.Redis.from_url(REDIS_URL)

generator = MockupGenerator()

# Prometheus metrics for GPU slot usage
GPU_SLOTS_IN_USE = Gauge("gpu_slots_in_use", "Number of GPU slots currently in use")
GPU_SLOT_ACQUIRE_TOTAL = Counter(
    "gpu_slot_acquire_total", "Total GPU slot acquisitions"
)


def get_gpu_slots() -> int:
    """Return the number of GPU slots defined in Redis or the default value."""
    value = redis_client.get("gpu_slots")
    if value is None:
        return DEFAULT_GPU_SLOTS
    try:
        return int(value)
    except ValueError:
        return DEFAULT_GPU_SLOTS


def queue_for_gpu(index: int) -> str:
    """Return the Celery queue name for ``index``."""
    return f"{GPU_QUEUE_PREFIX}-{index}"


def _acquire_gpu_lock(slot: int | None = None) -> RedisLock:
    """Acquire and return a lock for ``slot`` or any free slot."""
    while True:
        slots = [slot] if slot is not None else range(get_gpu_slots())
        for idx in slots:
            lock = redis_client.lock(
                f"gpu_slot:{idx}",
                timeout=GPU_LOCK_TIMEOUT,
                blocking_timeout=0,
            )
            if lock.acquire(blocking=False):
                return lock
        time.sleep(0.1)


@contextmanager
def gpu_slot(slot: int | None = None) -> Iterator[None]:
    """Yield while holding a GPU slot lock."""
    lock = _acquire_gpu_lock(slot)
    GPU_SLOTS_IN_USE.inc()
    GPU_SLOT_ACQUIRE_TOTAL.inc()
    try:
        yield
    finally:
        GPU_SLOTS_IN_USE.dec()
        lock.release()


@app.task(bind=True)  # type: ignore[misc]
def generate_mockup(
    self: Task, keywords_batch: list[list[str]], output_dir: str
) -> list[dict[str, object]]:
    """
    Generate mockups sequentially on the GPU.

    Args:
        keywords_batch: A list of keyword groups used to build prompts.
        output_dir: Directory where generated mockups will be written.

    Returns:
        A list of dictionaries containing image paths and listing metadata.
    """
    queue = self.request.delivery_info.get("routing_key", "")
    try:
        slot: int | None = int(queue.split("-")[-1])
    except (ValueError, AttributeError):
        slot = GPU_WORKER_INDEX if GPU_WORKER_INDEX >= 0 else None

    listing_gen = ListingGenerator()
    client = _get_storage_client()
    results: list[dict[str, object]] = []
    with gpu_slot(slot):
        for idx, keywords in enumerate(keywords_batch):
            context = PromptContext(keywords=keywords)
            prompt = build_prompt(context)
            output_path = Path(output_dir) / f"mockup_{idx}.png"
            gen_result = generator.generate(prompt, str(output_path))

            processed = remove_background(Image.open(gen_result.image_path))
            processed = convert_to_cmyk(processed)
            ensure_not_nsfw(processed)
            if not validate_dpi_image(processed):
                raise ValueError("Invalid DPI")
            if not validate_color_space(processed):
                raise ValueError("Invalid color space")
            compress_lossless(processed, output_path)
            obj_name = f"generated-mockups/{output_path.name}"
            if hasattr(client, "fput_object"):
                client.fput_object(settings.s3_bucket, obj_name, str(output_path))
            else:
                client.upload_file(str(output_path), settings.s3_bucket, obj_name)
            base = settings.s3_endpoint.rstrip("/") if settings.s3_endpoint else "s3://"
            uri = (
                f"{base}/{settings.s3_bucket}/{obj_name}"
                if settings.s3_endpoint
                else f"s3://{settings.s3_bucket}/{obj_name}"
            )
            metadata = listing_gen.generate(keywords)
            model_repository.save_generated_mockup(
                prompt,
                30,
                0,
                uri,
                metadata.title,
                metadata.description,
                metadata.tags,
            )
            results.append(
                {
                    "image_path": str(output_path),
                    "uri": uri,
                    "title": metadata.title,
                    "description": metadata.description,
                    "tags": metadata.tags,
                }
            )
        generator.cleanup()

    return results
