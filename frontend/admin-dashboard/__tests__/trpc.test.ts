import { trpc } from '../src/trpc';

jest.mock('../src/trpc', () => ({
  trpc: {
    ping: {
      mutate: jest.fn(),
    },
  },
}));

describe('tRPC ping', () => {
  it('calls trpc ping mutate', async () => {
    await trpc.ping.mutate();
    expect(trpc.ping.mutate).toHaveBeenCalled();
  });
});
