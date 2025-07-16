# Frontend

This directory contains Next.js applications. Build-time environment variables are loaded from `.env` files during `next build`.

The admin dashboard uses the following variables at build time:

- `REACT_APP_API_URL` – base URL for backend API requests.
- `REACT_APP_AUTH_TOKEN` – development authentication token.

Create a `.env` file based on `.env.example` before running `npm run build`.
