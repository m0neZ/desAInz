# Admin Dashboard

This is the frontend for the Admin Dashboard built with Next.js.

## Development

```bash
npm install
npm run dev
```

## Environment Variables

The dashboard reads the following variables at build time:

- `NEXT_PUBLIC_MONITORING_URL` - Base URL for the monitoring API. Defaults to
  `http://localhost:8000` when not specified.
