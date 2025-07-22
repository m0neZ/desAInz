"""Utilities for updating scoring engine weights."""

from __future__ import annotations

import logging
from typing import Iterable, Mapping

import numpy as np

import requests
from backend.shared.http import request_with_retry

logger = logging.getLogger(__name__)


def update_weights(
    api_url: str, metrics: Iterable[Mapping[str, float]]
) -> Mapping[str, float]:
    """Compute weights from metrics and update the scoring engine."""
    metrics_list = [dict(m) for m in metrics]
    cols = set().union(*(m.keys() for m in metrics_list))

    def arr(key: str) -> np.ndarray:
        return np.array([m.get(key, np.nan) for m in metrics_list], dtype=float)

    ctr = 0.0
    if {"clicks", "impressions"} <= cols:
        impressions_sum = float(np.nansum(arr("impressions")))
        ctr = (
            float(np.nansum(arr("clicks")) / impressions_sum)
            if impressions_sum
            else 0.0
        )
    elif {"favorites", "views"} <= cols:
        impressions_sum = float(np.nansum(arr("views")))
        ctr = (
            float(np.nansum(arr("favorites")) / impressions_sum)
            if impressions_sum
            else 0.0
        )
    elif "ctr" in cols:
        ctr = float(np.nanmean(arr("ctr")))

    conv_rate = 0.0
    if {"purchases", "clicks"} <= cols:
        clicks_sum = float(np.nansum(arr("clicks")))
        conv_rate = (
            float(np.nansum(arr("purchases")) / clicks_sum) if clicks_sum else 0.0
        )
    elif {"orders", "favorites"} <= cols:
        fav_sum = float(np.nansum(arr("favorites")))
        conv_rate = float(np.nansum(arr("orders")) / fav_sum) if fav_sum else 0.0
    elif {"orders", "views"} <= cols:
        views_sum = float(np.nansum(arr("views")))
        conv_rate = float(np.nansum(arr("orders")) / views_sum) if views_sum else 0.0
    elif {"conversions", "impressions"} <= cols:
        impressions_sum = float(np.nansum(arr("impressions")))
        conv_rate = (
            float(np.nansum(arr("conversions")) / impressions_sum)
            if impressions_sum
            else 0.0
        )
    elif "conversion_rate" in cols:
        conv_rate = float(np.nanmean(arr("conversion_rate")))

    weights = {
        "freshness": 1.0,
        "engagement": ctr,
        "novelty": 1.0,
        "community_fit": conv_rate,
        "seasonality": 1.0,
    }

    try:
        request_with_retry(
            "POST", f"{api_url}/weights/feedback", json=weights, timeout=5
        )
    except requests.RequestException as exc:
        logger.exception("failed to update weights: %s", exc)
        raise
    logger.info("updated weights: %s", weights)
    return weights
