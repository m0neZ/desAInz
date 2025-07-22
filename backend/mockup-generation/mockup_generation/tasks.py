"""Celery tasks for mockup generation."""

from __future__ import annotations

from pathlib import Path
from contextlib import asynccontextmanager
import subprocess
from typing import Any, AsyncIterator, cast
from dataclasses import dataclass, asdict
import signal
import sys

from aiobotocore.client import AioBaseClient
from aiobotocore.session import get_session
import hashlib
import os
import time
from botocore.exceptions import ClientError

from redis.lock import Lock as RedisLock
from redis.asyncio.lock import Lock as AsyncRedisLock
from celery import Task, chord
from prometheus_client import Counter, Gauge, Histogram
from opentelemetry import trace
from time import perf_counter

from PIL import Image
from .celery_app import app
from .generator import MockupGenerator

tracer = trace.get_tracer(__name__)


@dataclass(slots=True)
class MockupResult:
    """Result from successful mockup generation."""

    image_path: str
    uri: str
    title: str
    description: str
    tags: list[str]


@dataclass(slots=True)
class MockupError:
    """Error information for failed mockup generation."""

    error: str
    keywords: list[str]


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


@asynccontextmanager
async def _get_storage_client() -> AsyncIterator[AioBaseClient]:
    """Yield an asynchronous S3 client."""
    session = get_session()
    async with session.create_client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
    ) as client:
        yield client


MULTIPART_THRESHOLD = 16 * 1024 * 1024
"""Size in bytes above which multipart uploads are used."""

MULTIPART_CHUNK_SIZE = 8 * 1024 * 1024
"""Chunk size for multipart uploads."""


async def _multipart_upload(
    client: AioBaseClient,
    bucket: str,
    key: str,
    data: bytes,
    chunk_size: int = MULTIPART_CHUNK_SIZE,
) -> None:
    """Upload ``data`` to S3 using the multipart API."""
    resp = await client.create_multipart_upload(Bucket=bucket, Key=key)
    upload_id = resp["UploadId"]

    @dataclass(slots=True)
    class UploadedPart:
        """Information about a single uploaded part."""

        PartNumber: int
        ETag: str

    async def _upload(part_number: int, chunk: bytes) -> UploadedPart:
        part = await client.upload_part(
            Bucket=bucket,
            Key=key,
            UploadId=upload_id,
            PartNumber=part_number,
            Body=chunk,
        )
        return UploadedPart(part_number, part["ETag"])

    try:
        tasks = [
            asyncio.create_task(_upload(i, data[offset : offset + chunk_size]))
            for i, offset in enumerate(range(0, len(data), chunk_size), 1)
        ]
        parts: list[UploadedPart] = await asyncio.gather(*tasks)
        await client.complete_multipart_upload(
            Bucket=bucket,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={
                "Parts": sorted(
                    [asdict(p) for p in parts],
                    key=lambda p: int(cast(int, p["PartNumber"])),
                ),
            },
        )
    except Exception:
        await client.abort_multipart_upload(
            Bucket=bucket,
            Key=key,
            UploadId=upload_id,
        )
        raise


async def _upload_file(
    client: AioBaseClient,
    bucket: str,
    key: str,
    data: bytes,
) -> None:
    """Upload ``data`` using multipart if large enough."""
    if len(data) > MULTIPART_THRESHOLD:
        await _multipart_upload(client, bucket, key, data)
    else:
        await client.put_object(Bucket=bucket, Key=key, Body=data)


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
GPU_UTILIZATION = Gauge(
    "gpu_utilization_percent",
    "Current GPU utilization as reported by torch.cuda.utilization_rate",
)
GPU_TEMPERATURE = Gauge(
    "gpu_temperature_celsius",
    "Current GPU temperature in Celsius while generating mockups",
)


def _update_gpu_utilization() -> None:
    """Update the GPU utilization gauge using ``torch.cuda.utilization_rate``."""
    try:
        import torch

        available = getattr(torch.cuda, "is_available", lambda: False)()
        util_fn = getattr(torch.cuda, "utilization_rate", None)
        if available and callable(util_fn):
            try:
                GPU_UTILIZATION.set(float(util_fn()))
                return
            except Exception:  # pragma: no cover - optional runtime failure
                pass
    except Exception:  # pragma: no cover - torch unavailable
        pass
    GPU_UTILIZATION.set(0.0)


def _update_gpu_temperature() -> None:
    """Update the GPU temperature gauge using ``nvidia-smi`` when available."""
    try:
        import subprocess

        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        temp = float(result.stdout.strip().splitlines()[0])
        GPU_TEMPERATURE.set(temp)
        return
    except Exception:  # pragma: no cover - command may not exist
        pass
    GPU_TEMPERATURE.set(0.0)


def _update_gpu_metrics() -> None:
    """Update GPU utilization and temperature gauges."""
    _update_gpu_utilization()
    _update_gpu_temperature()


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
    """
    Yield while holding a GPU slot lock.

    The ``GPU_SLOTS_IN_USE`` gauge is incremented whenever a slot is acquired
    and decremented when released. Each successful acquisition also increments
    the ``GPU_SLOT_ACQUIRE_TOTAL`` counter.
    """
    lock = await _acquire_gpu_lock(slot)
    GPU_SLOTS_IN_USE.inc()
    GPU_SLOT_ACQUIRE_TOTAL.inc()
    try:
        yield
    finally:
        GPU_SLOTS_IN_USE.dec()
        await lock.release()
        _update_gpu_metrics()
        global _ACTIVE_LOCK
        _ACTIVE_LOCK = None


@app.task(bind=True)  # type: ignore[misc]
def generate_single_mockup(
    self: Task[Any, Any],
    keywords: list[str],
    output_dir: str,
    *,
    model: str | None = None,
    gpu_index: int | None = None,
    num_inference_steps: int = 30,
    index: int = 0,
) -> MockupResult | MockupError:
    """Generate a single mockup on the GPU."""
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

    async def runner() -> MockupResult | MockupError:
        async with gpu_slot(slot), _get_storage_client() as client:
            context = PromptContext(keywords=keywords)
            prompt = build_prompt(context)
            output_path = Path(output_dir) / f"mockup_{index}.png"
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
                with open(output_path, "rb") as fh:
                    data = fh.read()
                sha256 = hashlib.sha256(data).hexdigest()
                hashed_path = Path(output_dir) / f"{sha256}.png"
                Path(output_path).replace(hashed_path)
                output_path = hashed_path
                obj_name = f"generated-mockups/{sha256}.png"
                bucket = settings.s3_bucket or ""
                try:
                    await client.head_object(Bucket=bucket, Key=obj_name)
                except ClientError as exc:
                    if exc.response.get("Error", {}).get("Code") in {
                        "404",
                        "NotFound",
                        "NoSuchKey",
                    }:
                        await _upload_file(client, bucket, obj_name, data)
                        _invalidate_cdn_cache(obj_name)
                    else:
                        raise
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
                return MockupResult(
                    image_path=str(output_path),
                    uri=uri,
                    title=metadata.title,
                    description=metadata.description,
                    tags=metadata.tags,
                )
            except Exception as exc:  # pragma: no cover - error path tested separately
                return MockupError(error=str(exc), keywords=keywords)

    return asyncio.run(runner())


@app.task  # type: ignore[misc]
def _aggregate_mockups(
    results: list[MockupResult | MockupError],
) -> list[MockupResult | MockupError]:
    """Return aggregated mockup generation results."""
    return results


@app.task(bind=True)  # type: ignore[misc]
def generate_mockup(
    self: Task[Any, Any],
    keywords_batch: list[list[str]],
    output_dir: str,
    *,
    model: str | None = None,
    gpu_index: int | None = None,
    num_inference_steps: int = 30,
) -> list[MockupResult | MockupError]:
    """Generate mockups in parallel across available GPUs."""
    start = perf_counter()
    with tracer.start_as_current_span("generate_mockup"):
        try:
            if not hasattr(self.request, "id"):
                results = [
                    generate_single_mockup.run(
                        keywords,
                        output_dir,
                        model=model,
                        gpu_index=gpu_index,
                        num_inference_steps=num_inference_steps,
                        index=idx,
                    )
                    for idx, keywords in enumerate(keywords_batch)
                ]
            else:
                tasks = [
                    generate_single_mockup.s(
                        keywords,
                        output_dir,
                        model=model,
                        gpu_index=gpu_index,
                        num_inference_steps=num_inference_steps,
                        index=idx,
                    )
                    for idx, keywords in enumerate(keywords_batch)
                ]
                async_result = chord(tasks)(_aggregate_mockups.s())
                results = async_result.get()
            GENERATE_SUCCESS.inc()
            return results
        except Exception:
            GENERATE_FAILURE.inc()
            raise
        finally:
            GENERATE_DURATION.observe(perf_counter() - start)


# Register handlers on import so Celery workers clean up GPU locks on shutdown.
register_signal_handlers()
