# Feature Flags

Experimental functionality is gated using [Unleash](https://www.getunleash.io/).
The Marketplace Publisher service connects to an Unleash server to determine
whether a feature is enabled.

## Configuration

Set the following environment variables for services that consume feature flags:

| Variable | Description |
| --- | --- |
| `UNLEASH_URL` | Base URL of the Unleash API |
| `UNLEASH_TOKEN` | API token for authentication |
| `UNLEASH_APP_NAME` | Name of the application instance |

## Enabling Flags

Flags can be toggled from the Unleash dashboard. For local development you can
run a local Unleash server and set `UNLEASH_URL` accordingly. The flag used for
the staged rollout of the Shopify marketplace integration is
`shopify_integration`.

## Disabling Flags

To disable a feature, switch the corresponding toggle to **off** in the
Unleash UI. Clients automatically pick up the change.
