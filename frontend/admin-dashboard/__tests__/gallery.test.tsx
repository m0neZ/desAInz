import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Gallery } from '../src/components/Gallery';

global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () =>
      Promise.resolve({
        result: {
          items: [{ id: 1, imageUrl: '/img.png', title: 'foo' }],
          total: 1,
        },
      }),
  })
) as jest.Mock;

test('shows gallery items', async () => {
  const client = new QueryClient();
  render(
    <QueryClientProvider client={client}>
      <Gallery limit={1} />
    </QueryClientProvider>
  );
  expect(screen.getByTestId('gallery-loading')).toBeInTheDocument();
  await waitFor(() => screen.getByTestId('gallery'));
  expect(screen.getByAltText('foo')).toBeInTheDocument();
});
