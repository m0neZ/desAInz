import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AuditLogsPage from '../src/pages/dashboard/audit-logs';
import OptimizationsPage from '../src/pages/dashboard/optimizations';
import MetricsPage from '../src/pages/dashboard/metrics';
import SignalsPage from '../src/pages/dashboard/signals';
import MockupGalleryPage from '../src/pages/dashboard/mockup-gallery';
import MetricsChartsPage from '../src/pages/dashboard/metrics-charts';
import OptimizationRecommendationsPage from '../src/pages/dashboard/optimization-recommendations';

jest.mock('../src/trpc', () => ({
  trpc: {
    auditLogs: { list: () => Promise.resolve({ total: 0, items: [] }) },
    optimizations: { list: () => Promise.resolve([]) },
    metrics: {
      list: () => Promise.resolve(''),
      summary: () => Promise.resolve([]),
    },
    signals: { list: () => Promise.resolve([]) },
    mockups: { list: () => Promise.resolve([]) },
    recommendations: { list: () => Promise.resolve([]) },
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

  it('signals', () => {
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <SignalsPage />
      </QueryClientProvider>
    );
    expect(
      screen.getByRole('heading', { name: /signals/i })
    ).toBeInTheDocument();
  });

  it('mockup gallery', () => {
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <MockupGalleryPage />
      </QueryClientProvider>
    );
    expect(
      screen.getByRole('heading', { name: /mockup gallery/i })
    ).toBeInTheDocument();
  });

  it('metrics charts', () => {
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <MetricsChartsPage />
      </QueryClientProvider>
    );
    expect(
      screen.getByRole('heading', { name: /metrics charts/i })
    ).toBeInTheDocument();
  });

  it('optimization recommendations', () => {
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <OptimizationRecommendationsPage />
      </QueryClientProvider>
    );
    expect(
      screen.getByRole('heading', { name: /optimization recommendations/i })
    ).toBeInTheDocument();
  });
});
