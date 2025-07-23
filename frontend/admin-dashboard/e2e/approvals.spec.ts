import { test, expect } from '@playwright/test';
import { server } from './msw-server';
import { rest } from 'msw';

test.beforeAll(() => server.listen({ onUnhandledRequest: 'bypass' }));
test.afterAll(() => server.close());
test.afterEach(() => server.resetHandlers());

test('approve and reject runs', async ({ page }) => {
  server.use(
    rest.get('http://localhost:8000/approvals', (_req, res, ctx) =>
      res(ctx.json({ runs: ['run123'] }))
    ),
    rest.post('http://localhost:8000/approvals/run123', (_req, res, ctx) =>
      res(ctx.json({ status: 'approved' }))
    )
  );

  await page.goto('/approvals');
  await expect(page.getByText('run123')).toBeVisible();
  await page.getByRole('button', { name: /approve/i }).click();
  await expect(page.getByText('run123')).not.toBeVisible();

  server.use(
    rest.get('http://localhost:8000/approvals', (_req, res, ctx) =>
      res(ctx.json({ runs: ['run456'] }))
    ),
    rest.delete('http://localhost:8000/approvals/run456', (_req, res, ctx) =>
      res(ctx.json({ status: 'rejected' }))
    )
  );

  await page.reload();
  await expect(page.getByText('run456')).toBeVisible();
  await page.getByRole('button', { name: /reject/i }).click();
  await expect(page.getByText('run456')).not.toBeVisible();
});
