"""Celery tasks for mockup generation."""

from __future__ import annotations

from pathlib import Path
from contextlib import contextmanager, asynccontextmanager
import subprocess
from typing import Iterator, Any, AsyncIterator
import signal
import sys

from botocore.client import BaseClient
from minio import Minio
import os
import time

from redis.lock import Lock as RedisLock
from redis.asyncio.lock import Lock as AsyncRedisLock
from celery import Task
from prometheus_client import Counter, Gauge, Histogram
from time import perf_counter

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
    validate_dimensions,
    validate_file_size,
    validate_color_space,
    validate_dpi_image,
)
from backend.shared.config import settings
from . import model_repository


def _invalidate_cdn_cache(path: str) -> None:
    """Invalidate CDN caches for ``path`` if configured."""
    distribution = settings.cdn_distribution_id
    if not distribution:
        return
    script = Path(__file__).resolve().parents[2] / "scripts" / "invalidate_cache.sh"
    subprocess.run([str(script), distribution, f"/{path}"], check=True)


def _get_storage_client() -> Minio | BaseClient:
    """Return a MinIO or boto3 client based on environment configuration."""
    if settings.s3_endpoint and "amazonaws" not in settings.s3_endpoint:
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

import asyncio
from backend.shared.cache import (
    SyncRedis,
    AsyncRedis,
    get_sync_client,
    get_async_client,
)

redis_client: SyncRedis = get_sync_client()
async_redis_client: AsyncRedis = get_async_client()

generator = MockupGenerator()

# Hold the currently acquired GPU lock for cleanup on termination.
_ACTIVE_LOCK: AsyncRedisLock | None = None


def _release_on_signal(_signum: int, _frame: object | None = None) -> None:
    """Release any active GPU lock and clean up the generator."""
    global _ACTIVE_LOCK
    if _ACTIVE_LOCK is not None and _ACTIVE_LOCK.locked():
        try:
            asyncio.run(_ACTIVE_LOCK.release())
        finally:
            _ACTIVE_LOCK = None
    generator.cleanup()
    sys.exit(0)


def register_signal_handlers() -> None:
    """Register handlers for SIGTERM and SIGINT."""
    signal.signal(signal.SIGTERM, _release_on_signal)
    signal.signal(signal.SIGINT, _release_on_signal)


# Prometheus metrics for GPU slot usage
GPU_SLOTS_IN_USE = Gauge("gpu_slots_in_use", "Number of GPU slots currently in use")
GPU_SLOT_ACQUIRE_TOTAL = Counter(
    "gpu_slot_acquire_total", "Total GPU slot acquisitions"
)

# Task metrics
GENERATE_DURATION = Histogram(
    "generate_mockup_duration_seconds",
    "Time spent running generate_mockup",
)
GENERATE_SUCCESS = Counter(
    "generate_mockup_success_total",
    "Number of successful generate_mockup runs",
)
GENERATE_FAILURE = Counter(
    "generate_mockup_failure_total",
    "Number of failed generate_mockup runs",
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


async def _acquire_gpu_lock(slot: int | None = None) -> AsyncRedisLock:
    """Acquire and return a lock for ``slot`` or any free slot."""
    while True:
        slots = [slot] if slot is not None else range(get_gpu_slots())
        for idx in slots:
            lock = async_redis_client.lock(
                f"gpu_slot:{idx}",
                timeout=GPU_LOCK_TIMEOUT,
                blocking_timeout=0,
            )
            if await lock.acquire(blocking=False):
                global _ACTIVE_LOCK
                _ACTIVE_LOCK = lock
                return lock
        await asyncio.sleep(0.1)


@asynccontextmanager
async def gpu_slot(slot: int | None = None) -> AsyncIterator[None]:
    """Yield while holding a GPU slot lock."""
    lock = await _acquire_gpu_lock(slot)
    GPU_SLOTS_IN_USE.inc()
    GPU_SLOT_ACQUIRE_TOTAL.inc()
    try:
        yield
    finally:
        GPU_SLOTS_IN_USE.dec()
        await lock.release()
        global _ACTIVE_LOCK
        _ACTIVE_LOCK = None


@app.task(bind=True)  # type: ignore[misc]
def generate_mockup(
    self: Task[Any, Any],
    keywords_batch: list[list[str]],
    output_dir: str,
    *,
    model: str | None = None,
    gpu_index: int | None = None,
    num_inference_steps: int = 30,
) -> list[dict[str, object]]:
    """
    Generate mockups sequentially on the GPU.

    Parameters
    ----------
    self : Task
        Celery task instance.
    keywords_batch : list[list[str]]
        List of keyword groups used to build prompts.
    output_dir : str
        Directory where generated mockups will be written.
    model : str | None, optional
        Model identifier to use for generation.
    gpu_index : int | None, optional
        Preferred GPU slot index.
    num_inference_steps : int, optional
        Number of inference steps for the diffusion model.

    Returns
    -------
    list[dict[str, object]]
        Each item contains the image path and listing metadata. If a prompt
        fails, the item will include an ``error`` key with the message.
    """
    start = perf_counter()
    try:
        delivery_info: dict[str, Any] = dict(self.request.delivery_info or {})
        queue = str(delivery_info.get("routing_key", ""))
        try:
            slot: int | None = int(queue.split("-")[-1])
        except (ValueError, AttributeError):
            slot = (
                gpu_index
                if gpu_index is not None
                else (GPU_WORKER_INDEX if GPU_WORKER_INDEX >= 0 else None)
            )

        listing_gen = ListingGenerator()
        client = _get_storage_client()
        results: list[dict[str, object]] = []

        async def runner() -> list[dict[str, object]]:
            async with gpu_slot(slot):
                for idx, keywords in enumerate(keywords_batch):
                    context = PromptContext(keywords=keywords)
                    prompt = build_prompt(context)
                    output_path = Path(output_dir) / f"mockup_{idx}.png"
                    try:
                        gen_result = generator.generate(
                            prompt,
                            str(output_path),
                            num_inference_steps=num_inference_steps,
                            model_identifier=model,
                        )

                        processed = remove_background(Image.open(gen_result.image_path))
                        processed = convert_to_cmyk(processed)
                        ensure_not_nsfw(processed)
                        if not validate_dpi_image(processed):
                            raise ValueError("Invalid DPI")
                        if not validate_color_space(processed):
                            raise ValueError("Invalid color space")
                        if not validate_dimensions(processed):
                            raise ValueError("Invalid dimensions")
                        compress_lossless(processed, output_path)
                        if not validate_file_size(output_path):
                            raise ValueError("File size too large")
                        obj_name = f"generated-mockups/{output_path.name}"
                        bucket = settings.s3_bucket or ""
                        if hasattr(client, "fput_object"):
                            client.fput_object(bucket, obj_name, str(output_path))
                        else:
                            client.upload_file(str(output_path), bucket, obj_name)
                        _invalidate_cdn_cache(obj_name)
                        base = settings.s3_base_url or settings.s3_endpoint
                        if base:
                            base = base.rstrip("/")
                            uri = f"{base}/{settings.s3_bucket}/{obj_name}"
                        else:
                            uri = f"s3://{settings.s3_bucket}/{obj_name}"
                        metadata = listing_gen.generate(keywords)
                        model_repository.save_generated_mockup(
                            prompt,
                            num_inference_steps,
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
                    except (
                        Exception
                    ) as exc:  # pragma: no cover - error path tested separately
                        results.append({"error": str(exc), "keywords": keywords})
            return results

        results = asyncio.run(runner())
        generator.cleanup()
        GENERATE_SUCCESS.inc()
        return results
    except Exception:
        GENERATE_FAILURE.inc()
        raise
    finally:
        GENERATE_DURATION.observe(perf_counter() - start)


# Register handlers on import so Celery workers clean up GPU locks on shutdown.
register_signal_handlers()
