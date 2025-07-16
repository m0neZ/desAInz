import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  env: {
    MONITORING_URL: process.env.MONITORING_URL,
  },
};

export default nextConfig;
