"""Celery application for the scoring engine."""

from __future__ import annotations

from celery import Celery

from backend.shared.queue_metrics import register_redis_queue_collector
from .settings import settings

CELERY_BROKER_URL = settings.celery_broker_url
app = Celery("scoring_engine", broker=CELERY_BROKER_URL)
app.conf.result_backend = CELERY_BROKER_URL

register_redis_queue_collector()
