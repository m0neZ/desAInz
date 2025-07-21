"""Celery application for the scoring engine."""

from __future__ import annotations

import os

from celery import Celery

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
app = Celery("scoring_engine", broker=CELERY_BROKER_URL)
app.conf.result_backend = CELERY_BROKER_URL
