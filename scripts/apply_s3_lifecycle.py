"""Configure S3 or GCS lifecycle rules using the CLI."""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)


def _aws_cli() -> str:
    """Return path to the AWS CLI."""
    cli = subprocess.run(
        ["which", "aws"],
        check=False,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not cli:
        msg = "AWS CLI is required"
        raise RuntimeError(msg)
    return cli


def apply_policy(bucket: str, storage_class: str = "GLACIER") -> None:
    """Apply transition to ``storage_class`` after 365 days in ``bucket``."""
    policy: Dict[str, Any] = {
        "Rules": [
            {
                "ID": "ArchiveAfter12Months",
                "Filter": {"Prefix": ""},
                "Status": "Enabled",
                "Transitions": [{"Days": 365, "StorageClass": storage_class}],
            }
        ]
    }

    cmd = [
        _aws_cli(),
        "s3api",
        "put-bucket-lifecycle-configuration",
        "--bucket",
        bucket,
        "--lifecycle-configuration",
        json.dumps(policy),
    ]
    logger.info("Running %s", " ".join(cmd))
    subprocess.run(cmd, check=True)
    logger.info("Applied lifecycle policy to %s", bucket)


def main(argv: list[str]) -> int:
    """
    Run the lifecycle configuration utility.

    The bucket name can be supplied as the first CLI argument or via the
    ``BUCKET`` environment variable. The storage class defaults to
    ``GLACIER`` and can be overridden by a second CLI argument or the
    ``STORAGE_CLASS`` environment variable.
    """

    bucket = argv[0] if argv else os.environ.get("BUCKET")
    if not bucket:
        logger.error("Usage: apply_s3_lifecycle.py <bucket> [storage-class]")
        return 1
    if len(argv) > 2:
        logger.error("Usage: apply_s3_lifecycle.py <bucket> [storage-class]")
        return 1

    storage_class = (
        argv[1] if len(argv) == 2 else os.environ.get("STORAGE_CLASS", "GLACIER")
    )
    apply_policy(bucket, storage_class)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main(sys.argv[1:]))
