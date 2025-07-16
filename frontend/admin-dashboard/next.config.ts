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
};

export default nextConfig;
