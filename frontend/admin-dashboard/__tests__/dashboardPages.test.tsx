import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AuditLogsPage from '../src/pages/dashboard/audit-logs';
import OptimizationsPage from '../src/pages/dashboard/optimizations';
import MetricsPage from '../src/pages/dashboard/metrics';

jest.mock('../src/trpc', () => ({
  trpc: {
    auditLogs: { list: () => Promise.resolve({ total: 0, items: [] }) },
    optimizations: { list: () => Promise.resolve([]) },
    metrics: { list: () => Promise.resolve('') },
  },
}));

describe('dashboard data pages render', () => {
  it('audit logs', () => {
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <AuditLogsPage />
      </QueryClientProvider>
    );
    expect(
      screen.getByRole('heading', { name: /audit logs/i })
    ).toBeInTheDocument();
  });

  it('optimizations', () => {
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <OptimizationsPage />
      </QueryClientProvider>
    );
    expect(
      screen.getByRole('heading', { name: /optimizations/i })
    ).toBeInTheDocument();
  });

  it('metrics', () => {
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <MetricsPage />
      </QueryClientProvider>
    );
    expect(
      screen.getByRole('heading', { name: /metrics/i })
    ).toBeInTheDocument();
  });
});
