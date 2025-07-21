import type { NextConfig } from 'next';
import withPWA from 'next-pwa';

/**
 * Next.js configuration enabling tree shaking and granular code splitting.
 */
const nextConfig: NextConfig = {
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

export default withPWA({
  dest: 'public',
  disable: process.env.NODE_ENV === 'development',
})(nextConfig);
