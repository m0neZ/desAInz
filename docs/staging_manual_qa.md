# Manual QA in Staging

This document describes the steps for verifying new changes in the staging environment.

## Test Plan

### 1. Ingestion
1. Deploy the latest container images to the `staging` namespace.
2. Upload a sample dataset using `scripts/upload_signals.py --env staging sample.csv`.
3. Confirm ingestion jobs complete without errors using `kubectl logs`.

### 2. Scoring
1. Trigger the scoring workflow via the API Gateway:
   ```bash
   curl -X POST "$STAGING_API/scoring/run" -H "Authorization: Bearer $TOKEN"
   ```
2. Inspect the job status with `kubectl get jobs -n staging`.
3. Validate score outputs appear in the staging database.

### 3. Mock-up Creation
1. Submit a design request using the dashboard form.
2. Verify the `mockup-generation` pods create preview images.
3. Download the generated mock-ups from MinIO or S3.

### 4. Publishing
1. Trigger the publishing pipeline via the dashboard action.
2. Ensure items appear in the staging marketplace bucket.
3. Check CDN invalidation logs for successful cache busting.

### 5. Dashboard Operations
1. Log in to the admin dashboard at the staging URL.
2. Navigate through analytics, resource monitoring and job controls.
3. Confirm charts render and manual job triggers succeed.

## Results
Attempted execution on 2024-08-14. Deployment and curl commands were blocked by network restrictions in the Codex environment, so workflows could not be fully validated. Dashboard access was also unavailable. No application issues were observed locally, but staging results remain unverified.

## Reporting
Record any defects in GitHub issues with logs or screenshots. Include references to the steps above for reproducibility.

These checks help catch regressions before promoting a release to production.
