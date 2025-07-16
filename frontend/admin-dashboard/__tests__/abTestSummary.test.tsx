import { render, screen, waitFor } from '@testing-library/react';
import { AbTestSummary } from '../src/components/AbTestSummary';

global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ conversions: 2, impressions: 5 }),
  })
) as jest.Mock;

test('loads and displays summary', async () => {
  render(<AbTestSummary abTestId={1} />);
  expect(screen.getByTestId('abtest-loading')).toBeInTheDocument();
  await waitFor(() => screen.getByTestId('abtest-summary'));
  expect(screen.getByText(/Conversions/)).toBeInTheDocument();
});
