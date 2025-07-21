import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TrendingKeywords } from '../src/components/TrendingKeywords';

global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve(['foo', 'bar']),
  })
) as jest.Mock;

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient();
  return render(
    <QueryClientProvider client={client}>{ui}</QueryClientProvider>
  );
}

test('shows trending keywords', async () => {
  renderWithClient(<TrendingKeywords />);
  expect(screen.getByTestId('trending-loading')).toBeInTheDocument();
  await waitFor(() => screen.getByTestId('trending-keywords'));
  expect(screen.getByText('1. foo')).toBeInTheDocument();
});
