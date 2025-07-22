"""Tests for the S3 key rotation helper."""

from __future__ import annotations

import base64
import subprocess

import boto3
import pytest
from moto import mock_aws

pytestmark = pytest.mark.filterwarnings(
    r"ignore:datetime\.datetime\.utcnow\(\) is deprecated"
)

from scripts.rotate_s3_keys import rotate


@mock_aws
def test_rotate_s3_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """New keys are created and kubectl is called with encoded values."""
    iam = boto3.client("iam", region_name="us-east-1")
    iam.create_user(UserName="test")
    iam.create_access_key(UserName="test")
    called: list[list[str]] = []

    def fake_run(cmd: list[str], check: bool = True) -> None:
        called.append(cmd)

    monkeypatch.setattr(subprocess, "run", fake_run)
    creds = rotate("test", "s3-secret")

    keys = iam.list_access_keys(UserName="test")
    assert len(keys["AccessKeyMetadata"]) == 1
    patch = called[0]
    data_flag = patch[-1]
    encoded_id = base64.b64encode(creds["AWS_ACCESS_KEY_ID"].encode()).decode()
    assert encoded_id in data_flag
    encoded_secret = base64.b64encode(creds["AWS_SECRET_ACCESS_KEY"].encode()).decode()
    assert encoded_secret in data_flag
