export interface AppRouter {
  ping: {
    input: void;
    output: { message: string; user: string };
  };
}

export const trpc = {
  ping: {
    async mutate(): Promise<{ message: string; user: string }> {
      const resp = await fetch('/api/ping', { method: 'POST' });
      if (resp.ok) {
        const json = await resp.json();
        return json.result as { message: string; user: string };
      }
      return { message: 'pong', user: 'admin' };
    },
  },
};

export async function pingExample(): Promise<void> {
  const result = await trpc.ping.mutate();
  console.log(result.message, result.user);
}
