"""Celery configuration."""

from __future__ import annotations

import os
from typing import Iterable, cast

from celery import Celery
from celery.signals import worker_ready
from prometheus_client import REGISTRY
from prometheus_client.core import GaugeMetricFamily
import redis

from backend.shared.queue_metrics import register_redis_queue_collector

from .tasks import queue_for_gpu


CELERY_BROKER = os.getenv("CELERY_BROKER", "redis")
if CELERY_BROKER == "redis":
    host = os.getenv("REDIS_HOST", "localhost")
    port = os.getenv("REDIS_PORT", "6379")
    db = os.getenv("REDIS_DB", "0")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", f"redis://{host}:{port}/{db}")
    RESULT_BACKEND = CELERY_BROKER_URL
elif CELERY_BROKER == "rabbitmq":
    host = os.getenv("RABBITMQ_HOST", "localhost")
    port = os.getenv("RABBITMQ_PORT", "5672")
    user = os.getenv("RABBITMQ_USER", "guest")
    password = os.getenv("RABBITMQ_PASSWORD", "guest")
    CELERY_BROKER_URL = os.getenv(
        "CELERY_BROKER_URL", f"amqp://{user}:{password}@{host}:{port}//"
    )
    RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
elif CELERY_BROKER == "kafka":
    servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", f"kafka://{servers}")
    RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "rpc://")
else:  # pragma: no cover - invalid broker selection
    raise ValueError(f"Unsupported CELERY_BROKER: {CELERY_BROKER}")

app = Celery("mockup_generation", broker=CELERY_BROKER_URL)
app.conf.result_backend = RESULT_BACKEND
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True


class GPUQueueCollector:
    """Collect queue lengths for all GPU task queues."""

    def collect(self) -> Iterable[GaugeMetricFamily]:
        """Return metrics for pending tasks per queue."""
        if CELERY_BROKER != "redis":
            return []

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

register_redis_queue_collector()


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


@worker_ready.connect
def _autoscale_workers(sender: object, **_: object) -> None:
    """Autoscale based on configured GPU slots."""
    try:
        from .tasks import get_gpu_slots

        slots = get_gpu_slots()
        factor = int(os.getenv("GPU_AUTOSCALE_FACTOR", "2"))
        sender.app.control.autoscale(slots * factor, slots)
    except Exception:
        pass
