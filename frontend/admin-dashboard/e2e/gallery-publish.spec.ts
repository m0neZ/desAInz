import { test, expect } from '@playwright/test';
import { server } from './msw-server';

test.beforeAll(() => server.listen({ onUnhandledRequest: 'bypass' }));
test.afterAll(() => server.close());
test.afterEach(() => server.resetHandlers());

test('select mockup from gallery and publish', async ({ page }) => {
  await page.goto('/dashboard');
  await page.getByRole('link', { name: /gallery/i }).click();
  await expect(page).toHaveURL(/dashboard\/gallery/);

  const firstImage = page.getByRole('img').first();
  await firstImage.click();

  await expect(page).toHaveURL(/dashboard\/publish/);
  await expect(page.getByTestId('selected-mockup')).toBeVisible();
});
