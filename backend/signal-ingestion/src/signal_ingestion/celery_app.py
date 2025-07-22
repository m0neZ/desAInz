"""Celery application for signal ingestion."""

from __future__ import annotations

from celery import Celery

from backend.shared.queue_metrics import register_redis_queue_collector

from .settings import settings

app = Celery("signal_ingestion", broker=settings.celery_broker_url)
app.conf.result_backend = settings.celery_broker_url

register_redis_queue_collector()
