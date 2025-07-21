"""Manage AWS spot instances for Kubernetes nodes."""

from __future__ import annotations

import argparse
import subprocess
import time

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
    return resp["Instances"][0]["InstanceId"]


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


if __name__ == "__main__":
    main()
