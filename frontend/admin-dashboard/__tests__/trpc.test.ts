import { trpc } from '../src/trpc';

beforeEach(() => {
  global.fetch = jest.fn((url: string) => {
    if (url.includes('/audit-logs')) {
      return Promise.resolve({
        ok: true,
        json: async () => ({ total: 1, items: [] }),
      }) as unknown as Response;
    }
    if (url.includes('/optimizations')) {
      return Promise.resolve({
        ok: true,
        json: async () => ['opt'],
      }) as unknown as Response;
    }
    if (url.includes('/metrics')) {
      return Promise.resolve({
        ok: true,
        text: async () => 'm',
      }) as unknown as Response;
    }
    return Promise.resolve({
      ok: true,
      json: async () => ({ result: { message: 'pong', user: 'test' } }),
    }) as unknown as Response;
  });
});

afterEach(() => {
  (global.fetch as jest.Mock).mockRestore();
});

describe('tRPC ping', () => {
  it('calls fetch with ping route', async () => {
    const result = await trpc.ping.mutate();
    expect(global.fetch).toHaveBeenCalled();
    expect(result.message).toBe('pong');
  });
});

test('auditLogs.list fetches data', async () => {
  await trpc.auditLogs.list();
  expect(global.fetch).toHaveBeenCalledWith(
    'http://localhost:8000/audit-logs?page=1&limit=50'
  );
});

test('optimizations.list fetches data', async () => {
  await trpc.optimizations.list();
  expect(global.fetch).toHaveBeenCalledWith(
    'http://localhost:8000/optimizations'
  );
});

test('metrics.list fetches data', async () => {
  await trpc.metrics.list();
  expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/metrics');
});
