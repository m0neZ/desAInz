import { trpc } from '../src/trpc';

beforeEach(() => {
  global.fetch = jest.fn(
    () =>
      Promise.resolve({
        ok: true,
        json: async () => ({ result: { message: 'pong', user: 'test' } }),
      }) as unknown as Response
  );
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
