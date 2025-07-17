import { signIn, signOut, useSession } from 'next-auth/react';

function useSafeSession() {
  try {
    return useSession();
  } catch {
    return { data: null, status: 'unauthenticated' } as const;
  }
}

export default function AuthButton() {
  const { data: session, status } = useSafeSession();

  if (status === 'loading') {
    return null;
  }

  if (session) {
    return (
      <button onClick={() => signOut()} className="ml-auto">
        Logout
      </button>
    );
  }

  return (
    <button onClick={() => signIn()} className="ml-auto">
      Login
    </button>
  );
}
