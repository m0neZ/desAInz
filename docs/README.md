# Documentation

The `blueprints` folder contains the full system blueprint.

- [Design Idea Engine Complete Blueprint](blueprints/DesignIdeaEngineCompleteBlueprint.md)
- [Configuration](configuration.md)
- [Metrics Storage](metrics_storage.md)
- [Log Aggregation](logs_with_loki.md)
- [GPU Mockup Generation](mockup_generation.md)
- [Resource Requests](resource_requests.md)
- Kafka schemas under `schemas/` are loaded into the registry configured by `SCHEMA_REGISTRY_URL`.
- OpenAPI schemas under `openapi/` can be regenerated with `python scripts/generate_openapi.py`.
  Run `python scripts/update_openapi_changelog.py` afterwards to include version
  hashes and update the changelog automatically.

The `scripts` directory provides helper scripts for setting up storage and CDN resources:

- `setup_storage.sh` - create the S3/MinIO bucket structure.
  It can also configure lifecycle rules on AWS S3 buckets.
- `configure_cdn.sh` - create a CloudFront distribution
- `invalidate_cache.sh` - invalidate CDN caches when mockups change. The
  publisher triggers this script after each upload if `CDN_DISTRIBUTION_ID` is
  configured.
- Base Kubernetes manifests can be found in `infrastructure/k8s` with instructions for
  customizing them for local Minikube testing.
  Each script performs basic sanity checks and is safe to run multiple times.
Re-running them will validate the existing resources and skip changes when not needed.
This document merges the original project summary, system architecture, deployment guide, implementation plan and all earlier blueprint versions into one reference.

## Installing dependencies

Use pip and npm to install the packages required for running tests and building the documentation.

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
npm ci --legacy-peer-deps
```

Build the HTML documentation with:

```bash
make -C docs html
```

Execute the full test suite using:

```bash
make test
```

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
benchmark and run `scripts/run_load_tests.sh`. Continuous integration deploys a
temporary staging environment via the `loadtest` workflow and runs the
integration suite against AWS resources using an ephemeral bucket.

### Expected Throughput

Benchmark runs on a developer workstation yield roughly the following
transactions per second (TPS):

- API gateway: **80 TPS**
- Scoring engine: **60 TPS**
- Publisher: **40 TPS**

Numbers may vary depending on hardware and configuration, but significant
deviations should be investigated.

## Documentation Workflow

Documentation is automatically built and deployed via GitHub Actions. The
workflow defined in `.github/workflows/docs.yml` runs `make -C docs html`, which
invokes Sphinx with warnings treated as errors. `docformatter`,
`flake8-docstrings`, and `interrogate` are executed as part of the build
process. The generated
HTML is uploaded as an artifact and deployed to GitHub Pages using
`actions/deploy-pages` whenever changes are pushed to the `main` branch.
