import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FeatureFlagsList } from '../src/components/FeatureFlags/FeatureFlagsList';

beforeEach(() => {
  global.fetch = jest.fn((url: RequestInfo, init?: RequestInit) => {
    if (typeof url === 'string' && url.endsWith('/feature-flags')) {
      if (!init || init.method === 'GET') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ demo: false }),
        }) as unknown as Response;
      }
      return Promise.resolve({ ok: true }) as unknown as Response;
    }
    return Promise.resolve({ ok: true }) as unknown as Response;
  });
});

afterEach(() => {
  (global.fetch as jest.Mock).mockRestore();
});

test('lists and toggles flags', async () => {
  render(<FeatureFlagsList />);
  await waitFor(() => screen.getByLabelText('Feature flags'));
  const checkbox = screen.getByRole('checkbox');
  expect(checkbox).not.toBeChecked();
  await userEvent.click(checkbox);
  expect(global.fetch).toHaveBeenLastCalledWith(
    '/feature-flags/demo',
    expect.objectContaining({ method: 'POST' })
  );
});
