import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Heatmap } from '../src/components/Heatmap';

global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ result: [{ label: 'foo', count: 3 }] }),
  })
) as jest.Mock;

test('shows heatmap entries', async () => {
  const client = new QueryClient();
  render(
    <QueryClientProvider client={client}>
      <Heatmap />
    </QueryClientProvider>
  );
  expect(screen.getByTestId('heatmap-loading')).toBeInTheDocument();
  await waitFor(() => screen.getByTestId('heatmap'));
  expect(screen.getByText('foo: 3')).toBeInTheDocument();
});
