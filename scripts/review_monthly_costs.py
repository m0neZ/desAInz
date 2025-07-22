"""Utility to review monthly cost reports."""

from __future__ import annotations

import argparse
import csv
import logging
from pathlib import Path


def summarize(csv_file: Path) -> None:
    """Log summary statistics for a cost CSV file."""
    with csv_file.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        costs = {row["service"]: float(row["cost"] or 0.0) for row in reader}
    total = sum(costs.values())
    logger = logging.getLogger(__name__)
    logger.info("Total monthly cost: $%.2f", total)
    for service, value in sorted(costs.items(), key=lambda x: x[1], reverse=True):
        logger.info("- %s: $%.2f", service, value)


def main() -> None:
    """Entry point for the cost review script."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="CSV file with service,cost columns")
    args = parser.parse_args()
    summarize(args.file)


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    main()
