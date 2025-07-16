# Error Monitoring and Triage

Unhandled exceptions from backend services are sent to Sentry when `SENTRY_DSN` is configured. Each request middleware attaches a `correlation_id` which Sentry stores as a tag for easy filtering.

1. Sign in to the Sentry dashboard.
2. Select the environment matching your deployment.
3. Use the `correlation_id` tag to search for related events.
4. Review the stack trace and context to determine the root cause.
5. Resolve or ignore the issue once it has been addressed.

For local testing you can export `SENTRY_DSN` and run any service; captured errors will appear in your project shortly after triggering them.

