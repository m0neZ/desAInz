#!/usr/bin/env python3
"""Check coverage for specific packages."""
from __future__ import annotations

import sys
from pathlib import Path
from xml.etree import ElementTree as ET


def coverage_for_package(xml_path: Path, package: str) -> float:
    """Return coverage percentage for a package."""
    tree = ET.parse(xml_path)
    total = covered = 0
    package = package.rstrip("/")
    for cls in tree.findall(".//class"):
        filename = cls.get("filename", "")
        if filename.startswith(package):
            total += int(cls.get("lines-valid", "0"))
            covered += int(cls.get("lines-covered", "0"))
    if total == 0:
        return 100.0
    return 100.0 * covered / total


def main() -> None:
    """Entry point for package coverage check."""
    xml = Path("coverage.xml")
    if not xml.exists():
        print("coverage.xml not found", file=sys.stderr)
        sys.exit(1)

    packages = ["backend/scoring-engine", "backend/mockup-generation"]
    failed = False
    for pkg in packages:
        pct = coverage_for_package(xml, pkg)
        if pct < 100.0:
            print(f"{pkg} coverage {pct:.2f}% < 100%", file=sys.stderr)
            failed = True
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
