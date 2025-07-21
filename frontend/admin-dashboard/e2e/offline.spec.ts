import { test, expect } from '@playwright/test';

// Ensure the dashboard can be loaded from cache when offline.
test('dashboard accessible offline', async ({ page, context }) => {
  await page.goto('/dashboard');
  await page.waitForLoadState('networkidle');

  await context.setOffline(true);
  await page.reload();

  await expect(page).toHaveURL(/dashboard/);
  await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
});
