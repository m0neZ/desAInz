import { render, screen, waitFor } from '@testing-library/react';
import { AnalyticsChart } from '../src/components/AnalyticsChart';
import { LatencyChart } from '../src/components/LatencyChart';
import { AlertStatusIndicator } from '../src/components/AlertStatusIndicator';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

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
  const client = new QueryClient();
  render(
    <QueryClientProvider client={client}>
      <AnalyticsChart />
    </QueryClientProvider>
  );
  await waitFor(() => screen.getByTestId('analytics-chart'));
  expect(global.fetch).toHaveBeenCalledWith(
    '/api/monitoring/analytics?range=24h'
  );
});

test('latency chart loads data', async () => {
  const client = new QueryClient();
  render(
    <QueryClientProvider client={client}>
      <LatencyChart />
    </QueryClientProvider>
  );
  await waitFor(() => screen.getByTestId('latency-chart'));
  expect(global.fetch).toHaveBeenCalledWith(
    '/api/monitoring/latency?range=24h'
  );
});

test('alert indicator displays alert', async () => {
  const client = new QueryClient();
  render(
    <QueryClientProvider client={client}>
      <AlertStatusIndicator />
    </QueryClientProvider>
  );
  await waitFor(() => screen.getByText('ALERT'));
});
