import { test, expect } from '@playwright/test';

test('login and publish design', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: /login/i }).click();
  await expect(page).toHaveURL(/signin/);

  await page.goBack();

  await page.goto('/dashboard');
  await page.getByRole('link', { name: /gallery/i }).click();
  await expect(page).toHaveURL(/dashboard\/gallery/);

  await page.getByRole('link', { name: /publish tasks/i }).click();
  await expect(page).toHaveURL(/dashboard\/publish/);
  await expect(
    page.getByRole('heading', { name: /publish tasks/i })
  ).toBeVisible();
});
