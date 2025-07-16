"""Metric ingestion job."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterable

import pandas as pd
from backend.shared.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


def ingest_metrics(metrics: Iterable[dict[str, float]]) -> pd.DataFrame:
    """Persist incoming metrics and return DataFrame."""
    df = pd.DataFrame(metrics)
    if "timestamp" not in df.columns:
        df["timestamp"] = datetime.now(timezone.utc)
    logger.info("ingested %s metrics", len(df))
    return df
