"""Configure S3 lifecycle rules using boto3."""

from __future__ import annotations

import logging
import sys
from typing import Any, Dict

import boto3

logger = logging.getLogger(__name__)


def apply_policy(bucket: str) -> None:
    """Apply Glacier transition after 365 days to ``bucket``."""
    s3 = boto3.client("s3")
    lifecycle: Dict[str, Any] = {
        "Rules": [
            {
                "ID": "ArchiveAfter12Months",
                "Filter": {"Prefix": ""},
                "Status": "Enabled",
                "Transitions": [{"Days": 365, "StorageClass": "GLACIER"}],
            }
        ]
    }
    s3.put_bucket_lifecycle_configuration(
        Bucket=bucket, LifecycleConfiguration=lifecycle
    )
    logger.info("Applied lifecycle policy to %s", bucket)


def main(argv: list[str]) -> int:
    """CLI entrypoint."""
    if len(argv) != 1:
        print("Usage: apply_s3_lifecycle.py <bucket>", file=sys.stderr)
        return 1
    apply_policy(argv[0])
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main(sys.argv[1:]))
