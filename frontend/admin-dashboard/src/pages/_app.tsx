// @flow
import type { AppProps } from 'next/app';
import { UserProvider } from '@auth0/nextjs-auth0/client';
import '../styles/globals.css';
import AdminLayout from '../layouts/AdminLayout';
import { I18nProvider } from '../i18n';
import { TrpcProvider } from '../lib/trpc';

export default function MyApp({ Component, pageProps }: AppProps) {
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
