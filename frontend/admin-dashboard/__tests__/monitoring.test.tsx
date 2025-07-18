import { render, screen, waitFor } from '@testing-library/react';
import { AnalyticsChart } from '../src/components/AnalyticsChart';
import { LatencyChart } from '../src/components/LatencyChart';
import { AlertStatusIndicator } from '../src/components/AlertStatusIndicator';

beforeEach(() => {
  global.fetch = jest.fn((url: string) => {
    if (url.includes('analytics')) {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({ metrics: [{ timestamp: 't', value: 1 }] }),
      }) as unknown as Response;
    }
    return Promise.resolve({
      ok: true,
      json: () =>
        Promise.resolve({
          metrics: [{ timestamp: 't', value: 2 }],
          average_seconds: 8000,
        }),
    }) as unknown as Response;
  });
});

afterEach(() => {
  (global.fetch as jest.Mock).mockRestore();
});

test('analytics chart loads data', async () => {
  render(<AnalyticsChart />);
  await waitFor(() => screen.getByTestId('analytics-chart'));
  expect(global.fetch).toHaveBeenCalledWith(
    '/api/monitoring/analytics?range=24h'
  );
});

test('latency chart loads data', async () => {
  render(<LatencyChart />);
  await waitFor(() => screen.getByTestId('latency-chart'));
  expect(global.fetch).toHaveBeenCalledWith(
    '/api/monitoring/latency?range=24h'
  );
});

test('alert indicator displays alert', async () => {
  render(<AlertStatusIndicator />);
  await waitFor(() => screen.getByTestId('alert-status'));
  expect(screen.getByText('ALERT')).toBeInTheDocument();
});
