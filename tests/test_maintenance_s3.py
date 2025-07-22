"""Tests for the maintenance S3 utilities."""

from __future__ import annotations

import warnings
from datetime import datetime, timedelta

import boto3
import pytest
from moto import mock_aws

from backend.shared import config
from scripts import maintenance


@mock_aws
def test_purge_old_s3_objects(monkeypatch: pytest.MonkeyPatch) -> None:
    """Objects older than the retention period are removed."""
    s3 = boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    bucket = "test-bucket"
    s3.create_bucket(Bucket=bucket)
    s3.put_object(Bucket=bucket, Key="old.txt", Body=b"x")

    monkeypatch.setattr(
        maintenance,
        "datetime",
        type(
            "T",
            (datetime,),
            {"utcnow": classmethod(lambda cls: datetime.utcnow() + timedelta(days=91))},
        ),
    )
    monkeypatch.setattr(config.settings, "s3_bucket", bucket, raising=False)
    monkeypatch.setattr(config.settings, "s3_endpoint", None, raising=False)
    monkeypatch.setattr(config.settings, "s3_access_key", None, raising=False)
    monkeypatch.setattr(config.settings, "s3_secret_key", None, raising=False)

    maintenance.purge_old_s3_objects()

    remaining = s3.list_objects_v2(Bucket=bucket)
    assert "Contents" not in remaining
