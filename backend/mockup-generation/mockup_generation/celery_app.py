"""Celery configuration."""

from __future__ import annotations

import os

from celery import Celery
from prometheus_client import REGISTRY
from prometheus_client.core import GaugeMetricFamily
import redis
from typing import Iterable, cast

from .tasks import queue_for_gpu


CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
app = Celery("mockup_generation", broker=CELERY_BROKER_URL)
app.conf.result_backend = CELERY_BROKER_URL
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True


class GPUQueueCollector:
    """Collect queue lengths for all GPU task queues."""

    def collect(self) -> Iterable[GaugeMetricFamily]:
        """Return metrics for pending tasks per queue."""
        client = redis.Redis.from_url(CELERY_BROKER_URL)
        metric = GaugeMetricFamily(
            "gpu_queue_length",
            "Number of pending tasks per GPU queue",
            labels=["queue"],
        )
        try:
            import mockup_generation.tasks as tasks

            for idx in range(tasks.get_gpu_slots()):
                queue = tasks.queue_for_gpu(idx)
                metric.add_metric([queue], client.llen(queue))
        finally:
            client.close()
        return [metric]


try:
    REGISTRY.register(GPUQueueCollector())
except ValueError:  # pragma: no cover - collector already registered
    pass


def _route_gpu_tasks(
    name: str,
    args: tuple[object, ...],
    kwargs: dict[str, object],
    options: dict[str, object],
    **kws: object,
) -> dict[str, object]:
    """Route tasks with a ``gpu_index`` kwarg to the corresponding queue."""
    gpu = kwargs.get("gpu_index")
    if gpu is not None:
        options = {"queue": queue_for_gpu(int(cast(int, gpu)))}
    return options


app.conf.task_routes = (_route_gpu_tasks,)
