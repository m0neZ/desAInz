"""Start the Dagster webserver for the orchestrator."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def main() -> None:
    """Launch ``dagster-webserver`` with the standard configuration."""
    root_dir = Path(__file__).resolve().parents[1]
    os.chdir(root_dir)
    dagster_home = os.environ.get(
        "DAGSTER_HOME", str(root_dir / "backend" / "orchestrator")
    )
    os.environ["DAGSTER_HOME"] = dagster_home
    subprocess.run(
        [
            "dagster-webserver",
            "-w",
            "backend/orchestrator/workspace.yaml",
            "-h",
            "0.0.0.0",
            "-p",
            "3000",
        ],
        check=True,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
