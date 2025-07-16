export interface AppRouter {
  ping: {
    input: void;
    output: { message: string; user: string };
  };
  assignRole: {
    input: { userId: string; role: string };
    output: { status: string };
  };
}

export const trpc = {
  ping: {
    async mutate(): Promise<{ message: string; user: string }> {
      return { message: 'pong', user: 'admin' };
    },
  },
  assignRole: {
    async mutate({
      userId,
      role,
    }: {
      userId: string;
      role: string;
    }): Promise<{ status: string }> {
      const res = await fetch(`/roles/${userId}?role=${role}`, {
        method: 'POST',
      });
      return res.json();
    },
  },
};

export async function pingExample(): Promise<void> {
  const result = await trpc.ping.mutate();
  console.log(result.message, result.user);
}
