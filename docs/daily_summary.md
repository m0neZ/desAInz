# Daily Summary Report

`scripts/daily_summary.py` generates a JSON summary of the last 24 hours of activity. It reports:

- **ideas_generated** – number of ideas created
- **mockup_success_rate** – ratio of generated mockups to ideas
- **marketplace_stats** – count of successful listings per marketplace

Run the script manually or schedule it via cron:

```bash
./scripts/daily_summary.py
```
