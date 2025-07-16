"""Celery application for signal ingestion."""

from __future__ import annotations

import os

from celery import Celery


CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
app = Celery("signal_ingestion", broker=CELERY_BROKER_URL)
app.conf.result_backend = CELERY_BROKER_URL
