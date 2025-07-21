import type { NextConfig } from 'next';
import withPWA from 'next-pwa';
import type { RuntimeCaching } from 'next-pwa';
import bundleAnalyzer from '@next/bundle-analyzer';

/**
 * Next.js configuration enabling tree shaking and granular code splitting.
 */
const assetPrefix = process.env.NEXT_PUBLIC_CDN_BASE_URL ?? '';

const nextConfig: NextConfig = {
  assetPrefix,
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, s-maxage=600, stale-while-revalidate=300',
          },
        ],
      },
      {
        source: '/:path(health|metrics)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=60',
          },
        ],
      },
    ];
  },
  webpack: (config) => {
    config.optimization.usedExports = true;
    config.optimization.splitChunks = {
      chunks: 'all',
    };
    return config;
  },
};

const runtimeCaching: RuntimeCaching[] = [
  {
    urlPattern: /^https?.*\.(?:png|jpg|css|js|json)$/,
    handler: 'CacheFirst',
    options: {
      cacheName: 'static-assets',
      expiration: { maxEntries: 60, maxAgeSeconds: 7 * 24 * 60 * 60 },
    },
  },
  {
    urlPattern: /^https?.*\/api\/.*$/,
    handler: 'NetworkFirst',
    options: {
      cacheName: 'api-calls',
      networkTimeoutSeconds: 3,
      expiration: { maxEntries: 30, maxAgeSeconds: 5 * 60 },
    },
  },
];

const withBundleAnalyzer = bundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
});

export default withBundleAnalyzer(
  withPWA({
    dest: 'public',
    disable: process.env.NODE_ENV === 'development',
    runtimeCaching,
    register: true,
    skipWaiting: true,
  })(nextConfig)
);
