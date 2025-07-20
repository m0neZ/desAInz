"""Celery configuration."""

from __future__ import annotations

import os

from celery import Celery

from .tasks import queue_for_gpu


CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
app = Celery("mockup_generation", broker=CELERY_BROKER_URL)
app.conf.result_backend = CELERY_BROKER_URL


def _route_gpu_tasks(
    name: str, args: tuple, kwargs: dict, options: dict, **kws
) -> dict:
    """Route tasks with a ``gpu_index`` kwarg to the corresponding queue."""
    gpu = kwargs.get("gpu_index")
    if gpu is not None:
        options = {"queue": queue_for_gpu(int(gpu))}
    return options


app.conf.task_routes = (_route_gpu_tasks,)
