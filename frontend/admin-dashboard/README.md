# Admin Dashboard

This is the frontend for the Admin Dashboard built with Next.js.

## Development

```bash
npm install
npm run dev
```

## Build-time environment variables

The dashboard reads its monitoring endpoint from `NEXT_PUBLIC_MONITORING_URL` at
build time. During local development the variable can be left unset to fall back
to `http://localhost:8000/status`.
