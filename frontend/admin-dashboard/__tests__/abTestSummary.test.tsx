import { render, screen, waitFor } from '@testing-library/react';
import { AbTestSummary } from '../src/components/AbTestSummary';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ conversions: 2, impressions: 5 }),
  })
) as jest.Mock;

test('loads and displays summary', async () => {
  const client = new QueryClient();
  render(
    <QueryClientProvider client={client}>
      <AbTestSummary abTestId={1} />
    </QueryClientProvider>
  );
  expect(screen.getByTestId('abtest-loading')).toBeInTheDocument();
  await waitFor(() => screen.getByTestId('abtest-summary'));
  expect(screen.getByText(/Conversions/)).toBeInTheDocument();
});
