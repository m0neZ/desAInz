# Daily Summary Report

`scripts/daily_summary.py` generates a JSON summary of the last 24 hours of activity. It reports:

- **ideas_generated** – number of ideas created
- **mockup_success_rate** – ratio of generated mockups to ideas
- **marketplace_stats** – count of successful listings per marketplace

``generate_daily_summary`` accepts an optional ``session_provider`` parameter for
tests. By default it uses ``backend.shared.db.session_scope``.

Run the script manually or schedule it via cron:

```bash
./scripts/daily_summary.py
```

The monitoring service exposes the same information via the
`/daily_summary` HTTP endpoint:

```bash
curl http://monitoring:8000/daily_summary
```
