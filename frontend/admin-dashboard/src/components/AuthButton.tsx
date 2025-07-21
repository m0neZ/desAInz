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
      <button
        type="button"
        aria-label={t('logout')}
        onClick={() => signOut()}
        className="ml-auto"
      >
        {t('logout')}
      </button>
    );
  }

  return (
    <button
      type="button"
      aria-label={t('login')}
      onClick={() => signIn()}
      className="ml-auto"
    >
      {t('login')}
    </button>
  );
}
