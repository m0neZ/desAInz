# Admin Dashboard

This is the frontend for the Admin Dashboard built with Next.js.

## Development

```bash
npm install
npm run dev
npm run flow
```

## Analyzing the Bundle Size

Profile the production build and open the bundle analyzer report:

```bash
npm run analyze
```

## Environment Variables

The dashboard reads the following variables at build time:

- `NEXT_PUBLIC_MONITORING_URL` - Base URL for the monitoring API. Defaults to
  `http://localhost:8000` when not specified.
- `NEXT_PUBLIC_CDN_BASE_URL` - If set, static asset URLs are prefixed with this
  value so that content can be served through the CDN proxy.
- `NEXT_PUBLIC_WS_MAX_RETRIES` - Maximum number of times the dashboard will
  attempt to reconnect to the WebSocket metrics stream. Defaults to `5`.

### Auth0 Configuration

Authentication relies on the following Auth0 environment variables:

- `AUTH0_DOMAIN` - Your Auth0 tenant domain.
- `AUTH0_CLIENT_ID` - The client ID for the Auth0 application.
- `AUTH0_CLIENT_SECRET` - The client secret for the Auth0 application.
- `AUTH0_SECRET` - A random string used to encrypt cookies.
- `APP_BASE_URL` - Base URL for the dashboard (e.g. `http://localhost:3000`).
