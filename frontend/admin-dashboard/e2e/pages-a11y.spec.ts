import { test } from '@playwright/test';
import { checkA11y } from './a11y';

const routes = [
  '/',
  '/dashboard',
  '/dashboard/gallery',
  '/dashboard/publish',
  '/dashboard/audit-logs',
  '/dashboard/optimizations',
  '/dashboard/ab-tests',
  '/dashboard/analytics',
  '/dashboard/heatmap',
  '/dashboard/low-performers',
  '/dashboard/maintenance',
  '/dashboard/metrics',
  '/dashboard/preferences',
  '/dashboard/roles',
  '/dashboard/zazzle',
  '/ideas',
  '/metrics',
  '/mockups',
  '/publish',
  '/signals',
];

for (const route of routes) {
  test(`page ${route} has no accessibility violations`, async ({ page }) => {
    await page.goto(route);
    await checkA11y(page);
  });
}
