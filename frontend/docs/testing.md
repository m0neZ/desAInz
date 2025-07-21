# End-to-End Testing

This project uses **Playwright** for E2E tests located in `frontend/admin-dashboard/e2e`.
The tests run against the dashboard Docker image via `docker compose`.

## Running Tests Locally

```bash
npm run test:e2e
```

The command starts the dashboard container and executes Playwright with mocks powered by **MSW**.

## Continuous Integration

The CI workflow builds the dashboard image and runs the Playwright suite using that container. API calls are mocked so no external services are contacted.
