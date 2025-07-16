import { render, screen, waitFor } from '@testing-library/react';
import StatusIndicators from '../src/components/StatusIndicators';

beforeEach(() => {
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ cpu_percent: 10, memory_mb: 100 }),
  }) as jest.Mock;
});

afterEach(() => {
  jest.clearAllMocks();
});

test('renders status information', async () => {
  render(<StatusIndicators />);
  await waitFor(() => screen.getByText(/CPU:/));
  expect(screen.getByText(/CPU:/)).toBeInTheDocument();
});
