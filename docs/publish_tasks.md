# Manual Listing Overrides

Administrators can adjust listing metadata prior to publishing using the API Gateway.

`PATCH /publish-tasks/{task_id}` updates the stored metadata for a pending publish task. The body accepts arbitrary JSON fields used by the marketplace publisher.

`POST /publish-tasks/{task_id}/retry` re-triggers the publishing workflow for the task.

All edits and retries are recorded in the audit log.

If `SLACK_WEBHOOK_URL` is configured, failed publish attempts send a Slack notification.
When `PAGERDUTY_ROUTING_KEY` is set, the failure also triggers a PagerDuty alert.
