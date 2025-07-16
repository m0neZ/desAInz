import type { NextConfig } from 'next';

/**
 * Next.js configuration tuned for server-side rendering.
 * Adds caching headers to improve page performance.
 */
const nextConfig: NextConfig = {
  output: 'standalone',
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 's-maxage=60, stale-while-revalidate',
          },
        ],
      },
    ];
  },
};

export default nextConfig;
