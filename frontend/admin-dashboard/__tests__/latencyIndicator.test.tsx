import { render, screen, waitFor } from '@testing-library/react';
import LatencyIndicator from '../src/components/LatencyIndicator';

global.fetch = jest.fn(() =>
  Promise.resolve({ ok: true, json: () => Promise.resolve({ average_seconds: 7200 }) })
) as jest.Mock;

test('displays latency value', async () => {
  render(<LatencyIndicator />);
  await waitFor(() => screen.getByTestId('latency-indicator'));
  expect(screen.getByText(/Avg time from signal to publish/)).toBeInTheDocument();
});
