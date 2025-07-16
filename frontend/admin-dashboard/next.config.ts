import type { NextConfig } from 'next';

/**
 * Next.js configuration enabling tree shaking and granular code splitting.
 */
const nextConfig: NextConfig = {
  webpack: (config) => {
    config.optimization.usedExports = true;
    config.optimization.splitChunks = {
      chunks: 'all',
    };
    return config;
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, s-maxage=60, stale-while-revalidate=300',
          },
        ],
      },
    ];
  },
};

export default nextConfig;
