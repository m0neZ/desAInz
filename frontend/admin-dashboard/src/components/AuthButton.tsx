import { signIn, signOut, useSession } from 'next-auth/react';
import { useTranslation } from 'react-i18next';

function useSafeSession() {
  try {
    return useSession();
  } catch {
    return { data: null, status: 'unauthenticated' } as const;
  }
}

export default function AuthButton() {
  const { t } = useTranslation();
  const { data: session, status } = useSafeSession();

  if (status === 'loading') {
    return null;
  }

  if (session) {
    return (
      <button onClick={() => signOut()} className="ml-auto">
        {t('logout')}
      </button>
    );
  }

  return (
    <button onClick={() => signIn()} className="ml-auto">
      {t('login')}
    </button>
  );
}
