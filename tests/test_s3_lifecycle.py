"""Tests for the S3 lifecycle helper."""

from __future__ import annotations

import boto3
from moto import mock_aws

from scripts.apply_s3_lifecycle import apply_policy


@mock_aws
def test_apply_policy() -> None:
    """Lifecycle rule moves objects to Glacier after 365 days."""
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket = "test-bucket"
    s3.create_bucket(Bucket=bucket)

    apply_policy(bucket)

    config = s3.get_bucket_lifecycle_configuration(Bucket=bucket)
    rule = config["Rules"][0]
    transition = rule["Transitions"][0]
    assert transition["Days"] == 365
    assert transition["StorageClass"] == "GLACIER"
