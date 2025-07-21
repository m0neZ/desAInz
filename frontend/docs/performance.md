# Performance Monitoring

The admin dashboard includes tooling to inspect and improve bundle size.

## Bundle Analysis

Run `npm run analyze` within `frontend/admin-dashboard` to generate an HTML report showing the size of each bundle. The script sets `ANALYZE=true` and uses `@next/bundle-analyzer` under the hood.

## Code Splitting

Import heavy visualisation components using `next/dynamic` so that they load lazily when a user visits the relevant page. This keeps the initial bundle lean and improves start‑up times.

## Troubleshooting

If `next build --profile` fails with PostCSS errors, ensure `@tailwindcss/postcss` is installed and the PostCSS configuration references it correctly.
