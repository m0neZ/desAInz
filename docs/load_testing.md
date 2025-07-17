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

The `loadtest` GitHub Actions workflow runs automatically on every pull request
and on pushes to `main`. It starts a subset of the services and executes the
same script used locally. The workflow fails if the aggregate failure ratio
exceeds `1%` or if the average response time is above `1000ms`.
