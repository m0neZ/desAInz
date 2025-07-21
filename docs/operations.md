# Operations Guide

## Log Locations

Application logs are written to the directory defined by the `LOG_DIR` environment variable. When unset it defaults to `logs` inside the container. Each service writes its log files with a `.log` extension under this directory.

## Rotation Policy

A cron job executes `scripts/rotate_logs.py` daily at 01:00. The job moves log files into `LOG_DIR/archive` with a timestamp suffix and removes archives older than seven days. The cronjob definition can be found in `infrastructure/k8s/base/cronjobs/logrotate.yaml` and the Docker image used is built from `docker/logrotate`.


## Moderator Workflow

Moderators approve content generation runs from the Admin Dashboard.
Open the **Approvals** page to see a list of pending Dagster run IDs.
Click **Approve** next to a run to unblock publishing.
The API Gateway exposes `/approvals` for fetching pending runs and
`/approvals/{run_id}` for approving a run.

## Spot Instances

Use `scripts/manage_spot_instances.py` to request and release AWS spot nodes. A
typical workflow to add a worker is:

```bash
python scripts/manage_spot_instances.py request \
  --ami-id ami-12345678 \
  --instance-type g4dn.xlarge \
  --key-name kube-key \
  --security-group sg-12345678 \
  --subnet-id subnet-12345678
```

The script waits for the instance to become ready and labels the node so
Kubernetes can schedule pods on it. To remove a node run:

```bash
python scripts/manage_spot_instances.py release i-0abcd1234ef567890
```

Workers will checkpoint tasks using Celery's statedb so another node can resume
processing when a spot instance is reclaimed.

## Quota Handling

The signal ingestion service caches HTTP ``ETag`` headers in Redis. When a
resource has not changed, the adapter sends the cached value using the
``If-None-Match`` header and skips further processing when receiving a
``304 Not Modified`` response. This reduces bandwidth usage and helps stay
within third-party API quotas.

## Command Line Interface

``scripts/cli.py`` exposes operational helpers using subcommands.

### Ingest

Run a single ingestion cycle:

```bash
python scripts/cli.py ingest
```

### Score

Compute a score for a signal:

```bash
python scripts/cli.py score 0.5 0.1 0.2 0.3
```

### Generate Mockups

Generate an image for a prompt:

```bash
python scripts/cli.py generate-mockups "test prompt" --output-dir mockups
```

### Publish

Publish a design through the marketplace publisher:

```bash
python scripts/cli.py publish design.png redbubble
```
