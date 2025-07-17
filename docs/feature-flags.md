# Feature Flags

Experimental features are toggled using [Unleash](https://www.getunleash.io/).

## Enabling a flag

1. Start an Unleash server and create a feature with the desired name.
2. Set the environment variables `UNLEASH_URL` and `UNLEASH_API_TOKEN` in the service.
3. Optionally set `UNLEASH_APP_NAME` to override the default application name.
4. Restart the service to load the flag configuration.

Set ``UNLEASH_DEFAULTS`` to a JSON mapping of fallback values when no Unleash
server is configured or if it cannot be reached. Results are cached for the
number of seconds specified by ``UNLEASH_CACHE_TTL`` (default ``30``).

## Disabling a flag

Disable the feature from the Unleash dashboard or remove the environment
variables to fall back to all flags being disabled.

When the `society6_integration` flag is enabled, the marketplace publisher will
accept requests targeting the `society6` marketplace. When disabled, such
requests return HTTP 403.
