# Manual QA in Staging

This document describes the steps for verifying new changes in the staging environment.

1. **Deploy latest code**: The `Deploy to Staging` workflow runs every day. Ensure the workflow succeeded for the commit you want to test.
2. **Verify service health**:
   - Run `kubectl get pods -n staging` and confirm all pods are running.
   - Check application logs for errors using `kubectl logs`.
3. **Smoke test APIs**:
   - Use the API Gateway base URL for staging.
   - Test critical endpoints with `curl` or Postman.
4. **Check the admin dashboard**:
   - Navigate to the staging dashboard URL.
   - Log in with staging credentials and exercise key flows such as viewing metrics and triggering jobs.
5. **Data validation**:
   - Inspect the staging database or storage bucket to ensure data is processed correctly.
6. **Report issues**:
   - File a GitHub issue with screenshots or logs if any checks fail.

These checks help catch regressions before promoting a release to production.
