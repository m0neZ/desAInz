import type { NextConfig } from 'next';

/**
 * Next.js configuration enabling tree shaking and aggressive code splitting.
 * The `webpack` hook adjusts optimization settings while `esmExternals` allows
 * packages published as ES modules to be tree shaken.
 */
const nextConfig: NextConfig = {
  experimental: {
    esmExternals: 'loose',
  },
  webpack(config) {
    // Ensure unused exports are removed and common chunks are split automatically
    config.optimization.usedExports = true;
    config.optimization.splitChunks = {
      ...config.optimization.splitChunks,
      chunks: 'all',
    };
    return config;
  },
};

export default nextConfig;
