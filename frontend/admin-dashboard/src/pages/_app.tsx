import type { AppProps } from 'next/app';
import { UserProvider } from '@auth0/nextjs-auth0/client';
import '../styles/globals.css';
import AdminLayout from '../layouts/AdminLayout';
import { I18nProvider } from '../i18n';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '../lib/trpc';

export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <UserProvider>
      <QueryClientProvider client={queryClient}>
        <I18nProvider>
          <AdminLayout>
            <Component {...pageProps} />
          </AdminLayout>
        </I18nProvider>
      </QueryClientProvider>
    </UserProvider>
  );
}
