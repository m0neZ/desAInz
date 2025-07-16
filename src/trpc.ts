import { createTRPCProxyClient, httpBatchLink } from '@trpc/client';
import type { AppRouter } from '../backend/api-gateway/src/router';

/**
 * tRPC client configured to talk to the API Gateway's `/trpc` endpoint.
 */
export const trpc = createTRPCProxyClient<AppRouter>({
  links: [
    httpBatchLink({
      url: '/trpc',
    }),
  ],
});

/**
 * Example procedure call used to verify client setup.
 * The procedure should exist on the server; here we assume `ping` returns `pong`.
 */
export async function pingExample(): Promise<string> {
  return trpc.ping.query();
}
