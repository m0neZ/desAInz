"""Manage AWS spot instances for Kubernetes nodes."""

from __future__ import annotations

import argparse
import subprocess
import time
from typing import Iterable

import boto3


def request_instance(
    ami_id: str,
    instance_type: str,
    key_name: str,
    security_group: str,
    subnet_id: str,
    *,
    label: str = "node-role.kubernetes.io/spot=yes",
) -> str:
    """Request a spot instance and return its ID."""
    ec2 = boto3.client("ec2")
    resp = ec2.run_instances(
        ImageId=ami_id,
        InstanceType=instance_type,
        KeyName=key_name,
        SecurityGroupIds=[security_group],
        SubnetId=subnet_id,
        InstanceMarketOptions={"MarketType": "spot"},
        MinCount=1,
        MaxCount=1,
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [
                    {"Key": label.split("=")[0], "Value": label.split("=")[1]},
                ],
            }
        ],
    )
    return str(resp["Instances"][0]["InstanceId"])


def label_node(instance_id: str, label: str) -> None:
    """Label the Kubernetes node once it becomes available."""
    ec2 = boto3.client("ec2")
    while True:
        desc = ec2.describe_instances(InstanceIds=[instance_id])
        inst = desc["Reservations"][0]["Instances"][0]
        if inst["State"]["Name"] == "running" and "PrivateDnsName" in inst:
            break
        time.sleep(5)
    node_name = inst["PrivateDnsName"].split(".")[0]
    subprocess.run(
        ["kubectl", "label", "nodes", node_name, label, "--overwrite"],
        check=True,
    )


def release_instance(instance_id: str) -> None:
    """Terminate the given spot instance."""
    ec2 = boto3.client("ec2")
    ec2.terminate_instances(InstanceIds=[instance_id])


def _list_instances(label: str) -> list[str]:
    """Return IDs of running or pending instances matching the label."""
    ec2 = boto3.client("ec2")
    key, value = label.split("=")
    resp = ec2.describe_instances(
        Filters=[
            {"Name": f"tag:{key}", "Values": [value]},
            {"Name": "instance-state-name", "Values": ["pending", "running"]},
        ]
    )
    ids: list[str] = []
    for res in resp.get("Reservations", []):
        for inst in res.get("Instances", []):
            ids.append(inst["InstanceId"])
    return ids


def _ready_nodes(label: str) -> Iterable[str]:
    """Yield Kubernetes node names with the given label that are Ready."""
    cmd = ["kubectl", "get", "nodes", "-l", label, "--no-headers"]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "Ready":
            yield parts[0]


def maintain_nodes(
    ami_id: str,
    instance_type: str,
    key_name: str,
    security_group: str,
    subnet_id: str,
    *,
    label: str = "node-role.kubernetes.io/spot=yes",
    count: int = 1,
) -> None:
    """Ensure ``count`` spot nodes are available."""
    ready = list(_ready_nodes(label))
    missing = count - len(ready)
    if missing <= 0:
        return
    for _ in range(missing):
        instance_id = request_instance(
            ami_id,
            instance_type,
            key_name,
            security_group,
            subnet_id,
            label=label,
        )
        label_node(instance_id, label)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    req = sub.add_parser("request")
    req.add_argument("--ami-id", required=True)
    req.add_argument("--instance-type", required=True)
    req.add_argument("--key-name", required=True)
    req.add_argument("--security-group", required=True)
    req.add_argument("--subnet-id", required=True)
    req.add_argument("--label", default="node-role.kubernetes.io/spot=yes")

    rel = sub.add_parser("release")
    rel.add_argument("instance_id")

    maint = sub.add_parser("maintain")
    maint.add_argument("--ami-id", required=True)
    maint.add_argument("--instance-type", required=True)
    maint.add_argument("--key-name", required=True)
    maint.add_argument("--security-group", required=True)
    maint.add_argument("--subnet-id", required=True)
    maint.add_argument("--label", default="node-role.kubernetes.io/spot=yes")
    maint.add_argument("--count", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    """Entry point."""
    args = parse_args()
    if args.cmd == "request":
        instance_id = request_instance(
            args.ami_id,
            args.instance_type,
            args.key_name,
            args.security_group,
            args.subnet_id,
            label=args.label,
        )
        label_node(instance_id, args.label)
        print(instance_id)
    elif args.cmd == "release":
        release_instance(args.instance_id)
    elif args.cmd == "maintain":
        maintain_nodes(
            args.ami_id,
            args.instance_type,
            args.key_name,
            args.security_group,
            args.subnet_id,
            label=args.label,
            count=args.count,
        )


if __name__ == "__main__":
    main()
