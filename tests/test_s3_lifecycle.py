"""Tests for the S3 lifecycle helper script."""

from __future__ import annotations

import json
from unittest import mock

from scripts.apply_s3_lifecycle import apply_policy
from scripts.apply_s3_lifecycle import main


def test_apply_policy_invokes_cli() -> None:
    """Lifecycle policy is passed to the AWS CLI."""
    with mock.patch("subprocess.run") as run:
        with mock.patch("scripts.apply_s3_lifecycle._aws_cli", return_value="aws"):
            apply_policy("bucket", "GLACIER")
        assert run.call_count == 1
        cmd = run.call_args.args[0]
        assert cmd[:3] == [mock.ANY, "s3api", "put-bucket-lifecycle-configuration"]
        assert "--bucket" in cmd
        assert "bucket" in cmd
        # last element contains JSON with the storage class
        data = json.loads(cmd[-1])
        transition = data["Rules"][0]["Transitions"][0]
        assert transition["StorageClass"] == "GLACIER"


def test_main_env_vars(monkeypatch: mock.MagicMock) -> None:
    """``main`` falls back to environment variables."""
    monkeypatch.setenv("BUCKET", "envbucket")
    monkeypatch.setenv("STORAGE_CLASS", "DEEP_ARCHIVE")
    with mock.patch("scripts.apply_s3_lifecycle.apply_policy") as apply:
        assert main([]) == 0
        apply.assert_called_once_with("envbucket", "DEEP_ARCHIVE")
