"""Celery application for the scoring engine."""

from __future__ import annotations

from celery import Celery

from backend.shared.queue_metrics import register_redis_queue_collector

from .settings import settings

app = Celery("scoring_engine", broker=settings.celery_broker_url)
app.conf.result_backend = str(settings.celery_broker_url)

register_redis_queue_collector()
