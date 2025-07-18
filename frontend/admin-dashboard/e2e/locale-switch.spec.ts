import { test, expect } from '@playwright/test';

test('user can switch languages', async ({ page }) => {
  await page.goto('/');
  await page.getByTestId('lang-es').click();
  await expect(page.getByRole('heading', { name: /panel de administraci\u00f3n/i })).toBeVisible();
  await page.getByTestId('lang-en').click();
  await expect(page.getByRole('heading', { name: /admin dashboard/i })).toBeVisible();
});
