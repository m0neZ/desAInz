# Load Testing

The repository provides load tests for each API endpoint using [Locust](https://locust.io/).

## Baseline Scenarios

Baseline scenarios cover the ingestion, scoring and publishing APIs. They live in
`load_tests/baseline_scenarios.py` and are imported by `locustfile.py`. Each
scenario issues simple requests against its respective service to verify basic
performance characteristics.

## Running Locally

1. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt -r requirements-dev.txt
   pip install locust
   ```
2. Start the services you want to exercise. A minimal example is:
   ```bash
   python backend/service-template/src/main.py &
   python backend/monitoring/src/monitoring/main.py &
   python -m uvicorn backend.optimization.api:app --port 8003 &
   ```
3. Execute the load tests:
   ```bash
   ./scripts/run_load_tests.sh
   ```
   Adjust `USERS`, `SPAWN_RATE` and `RUN_TIME` environment variables to change the
   intensity.

## Continuous Integration

The `loadtest` workflow provisions a temporary staging namespace on each pull
request and push to `main`. Services are deployed to that namespace and an
ephemeral S3 bucket is created. The integration suite runs against these AWS
resources and all assets are removed once the run completes.
