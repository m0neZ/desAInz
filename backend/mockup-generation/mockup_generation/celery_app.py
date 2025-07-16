"""Celery configuration."""

from __future__ import annotations

import os

from celery import Celery

from backend.common.tracing import init_celery_tracing


CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
app = Celery("mockup_generation", broker=CELERY_BROKER_URL)
init_celery_tracing(app, "mockup-generation")
app.conf.result_backend = CELERY_BROKER_URL
