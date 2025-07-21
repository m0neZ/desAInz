# Admin Dashboard

This is the frontend for the Admin Dashboard built with Next.js.

## Development

```bash
npm install
npm run dev
npm run flow
```

## Environment Variables

The dashboard reads the following variables at build time:

- `NEXT_PUBLIC_MONITORING_URL` - Base URL for the monitoring API. Defaults to
  `http://localhost:8000` when not specified.

### Auth0 Configuration

Authentication relies on the following Auth0 environment variables:

- `AUTH0_DOMAIN` - Your Auth0 tenant domain.
- `AUTH0_CLIENT_ID` - The client ID for the Auth0 application.
- `AUTH0_CLIENT_SECRET` - The client secret for the Auth0 application.
- `AUTH0_SECRET` - A random string used to encrypt cookies.
- `APP_BASE_URL` - Base URL for the dashboard (e.g. `http://localhost:3000`).
