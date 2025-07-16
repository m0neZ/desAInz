"""Utility to review monthly cost reports."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def summarize(csv_file: Path) -> None:
    """Print summary statistics for a cost CSV file."""
    with csv_file.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        costs = {row["service"]: float(row["cost"] or 0.0) for row in reader}
    total = sum(costs.values())
    print(f"Total monthly cost: ${total:.2f}")
    for service, value in sorted(costs.items(), key=lambda x: x[1], reverse=True):
        print(f"- {service}: ${value:.2f}")


def main() -> None:
    """Entry point for the cost review script."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="CSV file with service,cost columns")
    args = parser.parse_args()
    summarize(args.file)


if __name__ == "__main__":  # pragma: no cover
    main()
