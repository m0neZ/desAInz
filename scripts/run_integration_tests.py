"""Run integration tests with strict settings."""

from __future__ import annotations

import subprocess
import sys


def main(argv: list[str] | None = None) -> None:
    """Execute pytest raising on warnings."""
    args = argv or sys.argv[1:]
    cmd = ["pytest", "-W", "error", "tests/integration", *args]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":  # pragma: no cover
    main()
