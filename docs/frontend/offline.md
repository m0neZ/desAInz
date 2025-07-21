# Offline Support

The admin dashboard uses a service worker provided by `next-pwa`.
Static assets such as images, scripts and stylesheets are cached
using a cache-first strategy. API calls required on startup are
cached with a network-first strategy to keep the data fresh while
still allowing the dashboard to load when the network is unavailable.

The service worker is automatically generated during `next build` and
served from the `public` directory. When a new version is deployed,
the worker skips the waiting phase so clients receive updates on the
next load.
