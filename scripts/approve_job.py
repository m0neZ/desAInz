"""CLI to approve Dagster runs via the approval service."""

from __future__ import annotations

import argparse
import logging
import os

import requests


def main() -> None:
    """Send approval for ``run_id`` to the configured service."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id", help="Dagster run ID")
    parser.add_argument(
        "--url",
        default=os.environ.get("APPROVAL_SERVICE_URL", "http://localhost:8000"),
        help="Base URL of the approval service",
    )
    args = parser.parse_args()
    resp = requests.post(f"{args.url}/approvals/{args.run_id}")
    resp.raise_for_status()
    logging.basicConfig(level=logging.INFO)
    logging.getLogger(__name__).info("approved")


if __name__ == "__main__":  # pragma: no cover
    main()
