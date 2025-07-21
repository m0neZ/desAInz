# Feature Flags

Experimental features are toggled using [LaunchDarkly](https://launchdarkly.com/) or environment variables.

## Enabling a flag

1. Provide a `LAUNCHDARKLY_SDK_KEY` to fetch flags from LaunchDarkly.
2. Set `FEATURE_FLAGS` to a JSON mapping of flag names to booleans for simple environment-based toggles.
3. Set `FEATURE_FLAGS_REDIS_URL` to read overrides from Redis if desired.
4. Results are cached for ``FEATURE_FLAGS_CACHE_TTL`` seconds (default ``30``).

## Disabling a flag

Disable the feature from the LaunchDarkly dashboard or remove the environment
variables to fall back to all flags being disabled.

When the `society6_integration` flag is enabled, the marketplace publisher will
accept requests targeting the `society6` marketplace. When disabled, such
requests return HTTP 403.
Similarly, the `zazzle_integration` flag controls access to the Zazzle publisher
API and gated UI links.

## API Management

Feature flags can be managed through the API Gateway. The following endpoints
require an authenticated user with the ``admin`` role:

* ``GET /feature-flags`` – list all known flags and their current values.
* ``POST /feature-flags/{name}`` – set the provided flag to the ``enabled``
  state in the request body.

The admin dashboard provides a simple interface built from the components in
``frontend/admin-dashboard/src/components/FeatureFlags`` which consume these
endpoints.
