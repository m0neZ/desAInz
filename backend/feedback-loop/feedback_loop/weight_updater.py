"""Utilities for updating scoring engine weights."""

from __future__ import annotations

import logging
from typing import Iterable, Mapping

import pandas as pd

import requests

logger = logging.getLogger(__name__)


def update_weights(
    api_url: str, metrics: Iterable[Mapping[str, float]]
) -> Mapping[str, float]:
    """Compute weights from metrics and update the scoring engine."""
    df = pd.DataFrame(metrics)
    ctr = 0.0
    if {"clicks", "impressions"} <= set(df.columns):
        impressions_sum = float(df["impressions"].sum())
        ctr = float(df["clicks"].sum() / impressions_sum) if impressions_sum else 0.0
    elif {"favorites", "views"} <= set(df.columns):
        impressions_sum = float(df["views"].sum())
        ctr = float(df["favorites"].sum() / impressions_sum) if impressions_sum else 0.0
    elif "ctr" in df.columns:
        ctr = float(df["ctr"].mean())

    conv_rate = 0.0
    if {"purchases", "clicks"} <= set(df.columns):
        clicks_sum = float(df["clicks"].sum())
        conv_rate = float(df["purchases"].sum() / clicks_sum) if clicks_sum else 0.0
    elif {"orders", "favorites"} <= set(df.columns):
        fav_sum = float(df["favorites"].sum())
        conv_rate = float(df["orders"].sum() / fav_sum) if fav_sum else 0.0
    elif {"orders", "views"} <= set(df.columns):
        views_sum = float(df["views"].sum())
        conv_rate = float(df["orders"].sum() / views_sum) if views_sum else 0.0
    elif {"conversions", "impressions"} <= set(df.columns):
        impressions_sum = float(df["impressions"].sum())
        conv_rate = (
            float(df["conversions"].sum() / impressions_sum) if impressions_sum else 0.0
        )
    elif "conversion_rate" in df.columns:
        conv_rate = float(df["conversion_rate"].mean())

    weights = {
        "freshness": 1.0,
        "engagement": ctr,
        "novelty": 1.0,
        "community_fit": conv_rate,
        "seasonality": 1.0,
    }

    response = requests.post(f"{api_url}/weights/feedback", json=weights, timeout=5)
    response.raise_for_status()
    logger.info("updated weights: %s", weights)
    return weights
