import { createTRPCProxyClient, httpBatchLink } from '@trpc/client';

/**
 * Types describing the available tRPC procedures.
 */
export interface AppRouter {
  ping: {
    input: void;
    output: { message: string; user: string };
  };
}

/**
 * TRPC client pointing to the API Gateway's `/trpc` endpoint.
 */
export const trpc = createTRPCProxyClient<AppRouter>({
  links: [
    httpBatchLink({
      url: '/trpc',
    }),
  ],
});

/** Example procedure call verifying types. */
export async function pingExample(): Promise<void> {
  const result = await trpc.ping.mutate();
  console.log(result.message, result.user);
}
