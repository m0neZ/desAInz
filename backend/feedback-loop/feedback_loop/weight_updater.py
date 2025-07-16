"""Utilities for updating scoring engine weights."""

from __future__ import annotations

import logging
from typing import Mapping

import requests
from backend.shared.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


def update_weights(api_url: str, weights: Mapping[str, float]) -> None:
    """Send weight updates to the scoring engine."""
    response = requests.put(f"{api_url}/weights", json=weights, timeout=5)
    response.raise_for_status()
    logger.info("updated weights: %s", weights)
