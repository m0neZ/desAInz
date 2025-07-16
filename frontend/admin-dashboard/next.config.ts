import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  webpack(config) {
    config.optimization.usedExports = true;
    config.optimization.splitChunks = { chunks: 'all' };
    return config;
  },
};

export default nextConfig;
