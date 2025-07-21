"""Synchronize listing states with the marketplace."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import requests
from apscheduler.schedulers.blocking import BlockingScheduler

from backend.shared.db import session_scope
from backend.shared.db.models import Listing

# Allow importing monitoring utilities
import sys

monitoring_path = Path(__file__).resolve().parents[1] / "backend" / "monitoring" / "src"
sys.path.append(str(monitoring_path))
from monitoring.pagerduty import notify_listing_issue  # noqa: E402

logger = logging.getLogger(__name__)

API_URL = os.environ.get("MARKETPLACE_API_URL", "https://api.redbubble.com")


def fetch_remote_state(listing_id: int) -> str:
    """Return the state for ``listing_id`` from the marketplace API."""
    resp = requests.get(f"{API_URL}/listings/{listing_id}", timeout=5)
    resp.raise_for_status()
    data: dict[str, Any] = resp.json()
    return str(data.get("state", "unknown"))


def sync_listing_states() -> int:
    """Update local listing states to match the marketplace."""
    updates = 0
    with session_scope() as session:
        listings = session.query(Listing).all()
        for listing in listings:
            try:
                remote_state = fetch_remote_state(listing.id)
            except requests.RequestException as exc:  # pragma: no cover
                logger.warning("failed to fetch listing %s: %s", listing.id, exc)
                continue
            if remote_state != listing.state:
                logger.info(
                    "Updating listing %s from %s to %s",
                    listing.id,
                    listing.state,
                    remote_state,
                )
                listing.state = remote_state
                updates += 1
                if remote_state in {"removed", "flagged"}:
                    notify_listing_issue(listing.id, remote_state)
        session.commit()
    return updates


def setup_scheduler() -> BlockingScheduler:
    """Return a scheduler configured for periodic listing sync."""
    scheduler = BlockingScheduler()
    scheduler.add_job(sync_listing_states, "interval", minutes=15)
    return scheduler


def main() -> None:
    """Run a single synchronization iteration."""
    sync_listing_states()


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    scheduler = setup_scheduler()
    scheduler.start()
