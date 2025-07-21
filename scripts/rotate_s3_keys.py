#!/usr/bin/env python
"""Create new S3 access keys and update Kubernetes secrets."""

from __future__ import annotations

import base64
import subprocess
from typing import Sequence

import boto3


def _create_keys(user: str) -> dict[str, str]:
    """Return newly created access keys for ``user`` deleting old ones."""
    iam = boto3.client("iam")
    resp = iam.create_access_key(UserName=user)
    new_key = resp["AccessKey"]
    for meta in iam.list_access_keys(UserName=user)["AccessKeyMetadata"]:
        if meta["AccessKeyId"] != new_key["AccessKeyId"]:
            iam.delete_access_key(UserName=user, AccessKeyId=meta["AccessKeyId"])
    return {
        "AWS_ACCESS_KEY_ID": new_key["AccessKeyId"],
        "AWS_SECRET_ACCESS_KEY": new_key["SecretAccessKey"],
    }


def _kubectl_patch(secret: str, data: dict[str, str]) -> None:
    """Patch ``secret`` with base64 encoded ``data`` via ``kubectl``."""
    encoded = {k: base64.b64encode(v.encode()).decode() for k, v in data.items()}
    patch = {"data": encoded}
    subprocess.run(
        ["kubectl", "patch", "secret", secret, "--type=merge", "-p", str(patch)],
        check=True,
    )


def rotate(user: str, secret: str) -> dict[str, str]:
    """Rotate S3 keys for ``user`` and update ``secret``."""
    creds = _create_keys(user)
    _kubectl_patch(secret, creds)
    return creds


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint."""
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("user", help="IAM user name")
    parser.add_argument("secret", help="Kubernetes secret name")
    args = parser.parse_args(list(argv) if argv is not None else None)
    rotate(args.user, args.secret)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
