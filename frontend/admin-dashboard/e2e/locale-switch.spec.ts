import { test, expect } from '@playwright/test';
import { checkA11y } from './a11y';

test('user can switch languages', async ({ page }) => {
  await page.goto('/');
  await page.getByTestId('lang-es').click();
  await expect(
    page.getByRole('heading', { name: /panel de administraci\u00f3n/i })
  ).toBeVisible();
  await checkA11y(page);
  await page.getByTestId('lang-en').click();
  await expect(
    page.getByRole('heading', { name: /admin dashboard/i })
  ).toBeVisible();
  await checkA11y(page);
});
