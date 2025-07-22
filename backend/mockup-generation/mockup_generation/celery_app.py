"""Celery configuration."""

from __future__ import annotations

from typing import Iterable, cast

from celery import Celery
from celery.signals import worker_ready
from prometheus_client import REGISTRY
from prometheus_client.core import GaugeMetricFamily
import redis

from backend.shared.queue_metrics import register_redis_queue_collector

from .tasks import queue_for_gpu
from .settings import settings


CELERY_BROKER = settings.celery_broker
if CELERY_BROKER == "redis":
    host = settings.redis_host
    port = settings.redis_port
    db = settings.redis_db
    CELERY_BROKER_URL = settings.celery_broker_url or f"redis://{host}:{port}/{db}"
    RESULT_BACKEND = CELERY_BROKER_URL
elif CELERY_BROKER == "rabbitmq":
    host = settings.rabbitmq_host
    port = settings.rabbitmq_port
    user = settings.rabbitmq_user
    password = settings.rabbitmq_password
    CELERY_BROKER_URL = (
        settings.celery_broker_url or f"amqp://{user}:{password}@{host}:{port}//"
    )
    RESULT_BACKEND = settings.celery_result_backend or CELERY_BROKER_URL
elif CELERY_BROKER == "kafka":
    servers = settings.kafka_bootstrap_servers
    CELERY_BROKER_URL = settings.celery_broker_url or f"kafka://{servers}"
    RESULT_BACKEND = settings.celery_result_backend or "rpc://"
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
        factor = settings.gpu_autoscale_factor
        sender.app.control.autoscale(slots * factor, slots)
    except Exception:
        pass
