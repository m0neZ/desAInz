import { render, screen } from '@testing-library/react';
import SignalsPage from '../app/signals/page';
import IdeasPage from '../app/ideas/page';
import MockupsPage from '../app/mockups/page';
import PublishPage from '../app/publish/page';
import MetricsPage from '../app/metrics/page';

jest.mock('../src/trpc', () => ({
  trpc: {
    signals: { list: () => Promise.resolve([]) },
    ideas: { list: () => Promise.resolve([]) },
    mockups: { list: () => Promise.resolve([]) },
    publishTasks: { list: () => Promise.resolve([]) },
    analytics: {
      summary: () => Promise.resolve({ revenue: 0, conversions: 0 }),
    },
  },
}));

describe('dashboard pages render', () => {
  it('signals', () => {
    render(<SignalsPage />);
    expect(
      screen.getByRole('heading', { name: /signals/i })
    ).toBeInTheDocument();
  });

  it('ideas', () => {
    render(<IdeasPage />);
    expect(screen.getByRole('heading', { name: /ideas/i })).toBeInTheDocument();
  });

  it('mockups', () => {
    render(<MockupsPage />);
    expect(
      screen.getByRole('heading', { name: /mockups/i })
    ).toBeInTheDocument();
  });

  it('publish', () => {
    render(<PublishPage />);
    expect(
      screen.getByRole('heading', { name: /publish tasks/i })
    ).toBeInTheDocument();
  });

  it('metrics', () => {
    render(<MetricsPage />);
    expect(
      screen.getByRole('heading', { name: /metrics/i })
    ).toBeInTheDocument();
  });
});
