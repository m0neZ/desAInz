# Documentation

The `blueprints` folder contains the full system blueprint.

- [Design Idea Engine Complete Blueprint](blueprints/DesignIdeaEngineCompleteBlueprint.md)
- [Sphinx Documentation](sphinx/index)

The `scripts` directory provides helper scripts for setting up storage and CDN resources:

- `setup_storage.sh` – create the S3/MinIO bucket structure
- `configure_cdn.sh` – create a CloudFront distribution
- `invalidate_cache.sh` – invalidate CDN caches when mockups change
  This document merges the original project summary, system architecture, deployment guide, implementation plan and all earlier blueprint versions into one reference.

## Monitoring Service

The monitoring service exposes a `/daily-summary` endpoint that reports the
ideas generated in the last 24 hours, the mockup success rate and publishing
counts for each marketplace. If the time from signal ingestion to publishing
exceeds two hours, a PagerDuty alert is triggered automatically.

## Service Template

The `backend/service-template` directory contains a minimal FastAPI service. The
application loads configuration from environment variables using
`pydantic.BaseSettings`. Variables can be provided via a `.env` file. The
`Settings` class is defined in `src/settings.py` and read on startup.
