import { trpc } from '../src/trpc';

jest.mock('../src/trpc', () => ({
  trpc: {
    ping: {
      mutate: jest.fn(),
    },
    assignRole: {
      mutate: jest.fn(),
    },
  },
}));

describe('tRPC ping', () => {
  it('calls trpc ping mutate', async () => {
    await trpc.ping.mutate();
    expect(trpc.ping.mutate).toHaveBeenCalled();
  });

  it('calls assignRole mutate', async () => {
    await trpc.assignRole.mutate({ userId: 'u1', role: 'viewer' });
    expect(trpc.assignRole.mutate).toHaveBeenCalledWith({
      userId: 'u1',
      role: 'viewer',
    });
  });
});
