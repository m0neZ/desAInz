import { render, screen } from '@testing-library/react';
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
    render(<AuditLogsPage />);
    expect(
      screen.getByRole('heading', { name: /audit logs/i })
    ).toBeInTheDocument();
  });

  it('optimizations', () => {
    render(<OptimizationsPage />);
    expect(
      screen.getByRole('heading', { name: /optimizations/i })
    ).toBeInTheDocument();
  });

  it('metrics', () => {
    render(<MetricsPage />);
    expect(
      screen.getByRole('heading', { name: /metrics/i })
    ).toBeInTheDocument();
  });
});
