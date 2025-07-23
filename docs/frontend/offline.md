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

## Testing offline mode

To verify offline support locally:

1. Run `npm run build` inside `frontend/admin-dashboard`.
2. Start the production server with `npm start` or serve the exported `out` directory using `npx serve out`.
3. Open the application in Chrome and go to **Application > Service Workers** in DevTools.
   Confirm that `service-worker.js` is installed and activated.
4. In the **Network** tab, enable the **Offline** checkbox.
5. Reload the page; the dashboard should load normally using cached assets.

Disable offline mode to restore normal connectivity.
