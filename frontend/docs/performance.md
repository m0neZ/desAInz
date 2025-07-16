# Performance Monitoring

The `next build --profile` command was executed to gather bundle size information. The build failed because Tailwind CSS was configured as a direct PostCSS plugin. The error message suggested installing `@tailwindcss/postcss` and updating the PostCSS configuration.

```
Import trace for requested module:
./src/styles/globals.css

> Build failed because of webpack errors
```
