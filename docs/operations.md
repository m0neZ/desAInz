# Operations Guide

## Log Locations

Application logs are written to the directory defined by the `LOG_DIR` environment variable. When unset it defaults to `logs` inside the container. Each service writes its log files with a `.log` extension under this directory.

## Rotation Policy

A cron job executes `scripts/rotate_logs.py` daily at 01:00. The job moves log files into `LOG_DIR/archive` with a timestamp suffix and removes archives older than seven days. The cronjob definition can be found in `infrastructure/k8s/base/cronjobs/logrotate.yaml` and the Docker image used is built from `docker/logrotate`.

