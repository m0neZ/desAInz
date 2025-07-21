import { test, expect } from '@playwright/test';
import { server } from './msw-server';

test.beforeAll(() => server.listen({ onUnhandledRequest: 'bypass' }));
test.afterAll(() => server.close());
test.afterEach(() => server.resetHandlers());

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

  await page.getByRole('link', { name: /audit logs/i }).click();
  await expect(page).toHaveURL(/dashboard\/audit-logs/);

  await page.getByRole('link', { name: /optimizations/i }).click();
  await expect(page).toHaveURL(/dashboard\/optimizations/);
});
