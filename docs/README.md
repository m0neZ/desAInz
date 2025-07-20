# Documentation

The `blueprints` folder contains the full system blueprint.

- [Design Idea Engine Complete Blueprint](blueprints/DesignIdeaEngineCompleteBlueprint.md)
- [Configuration](configuration.md)
- [Metrics Storage](metrics_storage.md)
- [Log Aggregation](logs_with_loki.md)
- [GPU Mockup Generation](mockup_generation.md)
- Kafka schemas under `schemas/` are loaded into the registry configured by `SCHEMA_REGISTRY_URL`.
- OpenAPI schemas under `openapi/` can be regenerated with `python scripts/generate_openapi.py`.

The `scripts` directory provides helper scripts for setting up storage and CDN resources:

- `setup_storage.sh` - create the S3/MinIO bucket structure.
  It can also configure lifecycle rules on AWS S3 buckets.
- `configure_cdn.sh` - create a CloudFront distribution
- `invalidate_cache.sh` - invalidate CDN caches when mockups change
- Base Kubernetes manifests can be found in `infrastructure/k8s` with instructions for
  customizing them for local Minikube testing.
  This document merges the original project summary, system architecture, deployment guide, implementation plan and all earlier blueprint versions into one reference.

Example lifecycle rule for AWS S3 buckets:

```bash
aws s3api put-bucket-lifecycle-configuration --bucket <bucket> \
  --lifecycle-configuration '{"Rules":[{"ID":"ArchiveOld","Status":"Enabled",\
"Filter":{"Prefix":""},"Transitions":[{"Days":365,"StorageClass":"GLACIER"}]}]}'
```

## Service Template

The `backend/service-template` directory contains a minimal FastAPI service. The
application loads configuration from environment variables using
`pydantic.BaseSettings`. Variables can be provided via a `.env` file for local
development or via Docker/Kubernetes secrets mounted under `/run/secrets`. The
`Settings` class is defined in `src/settings.py` and read on startup.

## Load Testing

Load tests use [Locust](https://locust.io/) and live in the `load_tests`
directory. To exercise the endpoints locally, start the services you want to
benchmark and run `scripts/run_load_tests.sh`. Continuous integration executes
the same script via the `loadtest` workflow.

### Expected Throughput

Benchmark runs on a developer workstation yield roughly the following
transactions per second (TPS):

- API gateway: **80 TPS**
- Scoring engine: **60 TPS**
- Publisher: **40 TPS**

Numbers may vary depending on hardware and configuration, but significant
deviations should be investigated.
