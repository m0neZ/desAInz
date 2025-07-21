# Monitoring Service

Collects metrics and exposes health endpoints for desAInz.

## Environment Variables

Copy `.env.example` to `.env` and configure as needed.

Required variables include:

- `LOG_FILE` – Path to the log output file (must end with `.log`).
- `SLA_THRESHOLD_HOURS` – SLA breach threshold in hours.
- `SLA_ALERT_COOLDOWN_MINUTES` – Minimum minutes between alerts.
- `ENABLE_PAGERDUTY` – Enable or disable PagerDuty integration.
