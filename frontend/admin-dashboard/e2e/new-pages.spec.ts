import { test, expect } from '@playwright/test';
import { server } from './msw-server';

test.beforeAll(() => server.listen({ onUnhandledRequest: 'bypass' }));
test.afterAll(() => server.close());
test.afterEach(() => server.resetHandlers());

test('visit new dashboard pages', async ({ page }) => {
  await page.goto('/dashboard/signals');
  await expect(page.getByRole('heading', { name: /signals/i })).toBeVisible();

  await page.goto('/dashboard/mockup-gallery');
  await expect(
    page.getByRole('heading', { name: /mockup gallery/i })
  ).toBeVisible();

  await page.goto('/dashboard/metrics-charts');
  await expect(
    page.getByRole('heading', { name: /metrics charts/i })
  ).toBeVisible();

  await page.goto('/dashboard/optimization-recommendations');
  await expect(
    page.getByRole('heading', { name: /optimization recommendations/i })
  ).toBeVisible();
});
