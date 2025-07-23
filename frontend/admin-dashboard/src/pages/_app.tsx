// @flow
import type { AppProps } from 'next/app';
import { UserProvider, useUser } from '@auth0/nextjs-auth0/client';
import '../styles/globals.css';
import AdminLayout from '../layouts/AdminLayout';
import { I18nProvider } from '../i18n';
import { TrpcProvider } from '../lib/trpc';
import { useEffect } from 'react';
import { useUserStore } from '../store/useUserStore';

export default function MyApp({ Component, pageProps }: AppProps) {
  const { user } = useUser();
  const setAuth = useUserStore((s) => s.setAuthenticated);

  useEffect(() => {
    setAuth(Boolean(user));
  }, [user, setAuth]);
  return (
    <UserProvider>
      <TrpcProvider>
        <I18nProvider>
          <AdminLayout>
            <Component {...pageProps} />
          </AdminLayout>
        </I18nProvider>
      </TrpcProvider>
    </UserProvider>
  );
}
