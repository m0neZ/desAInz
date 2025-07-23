"""Start the Dagster scheduler daemon."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def main() -> None:
    """Run ``dagster-daemon`` with the default configuration."""
    root_dir = Path(__file__).resolve().parents[1]
    os.chdir(root_dir)
    dagster_home = os.environ.get(
        "DAGSTER_HOME", str(root_dir / "backend" / "orchestrator")
    )
    os.environ["DAGSTER_HOME"] = dagster_home
    subprocess.run(["dagster-daemon", "run"], check=True)


if __name__ == "__main__":  # pragma: no cover
    main()
