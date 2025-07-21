import type { PlaywrightTestConfig } from '@playwright/test';

const config: PlaywrightTestConfig = {
  testDir: './e2e',
  webServer: {
    command:
      '(cd ../.. && docker compose -f docker-compose.dev.yml -f docker-compose.test.yml up admin-dashboard)',
    port: 3000,
    timeout: 120_000,
    reuseExistingServer: true,
  },
  use: {
    baseURL: 'http://localhost:3000',
  },
};

export default config;
