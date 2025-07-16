# Feature Flags

This project uses [Unleash](https://www.getunleash.io/) to manage experimental and staged features.

## Enabling a Flag

1. Deploy or access an Unleash server.
2. Create the desired feature toggle in the Unleash UI.
3. Set the `UNLEASH_URL` and `UNLEASH_TOKEN` environment variables for the service.
4. Enable the toggle for the environment specified by `UNLEASH_ENVIRONMENT`.

## Disabling a Flag

Toggle the feature off in the Unleash UI or remove the flag from the desired environment.

The `enable_printful` flag controls rollout of the Printful marketplace integration. Disable this flag to prevent the service from using the new integration.
