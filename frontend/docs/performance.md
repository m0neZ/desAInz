# Dashboard Performance

This document tracks the bundle sizes and optimizations for the admin dashboard.

## Build profiling

Attempting to run `next build --profile` failed due to a Tailwind CSS PostCSS
plugin error:

```
Error: It looks like you're trying to use `tailwindcss` directly as a PostCSS plugin. The PostCSS plugin has moved to a separate package, so to continue using Tailwind CSS with PostCSS you'll need to install `@tailwindcss/postcss` and update your PostCSS configuration.
```

Dynamic imports have been added for dashboard features to keep bundles small.
Once the Tailwind configuration is updated, rerun the profile build to capture
bundle sizes.
