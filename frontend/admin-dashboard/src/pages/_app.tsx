import type { AppProps } from 'next/app';
import type { Session } from 'next-auth';
import { SessionProvider } from 'next-auth/react';
import '../styles/globals.css';
import AdminLayout from '../layouts/AdminLayout';
import { I18nProvider } from '../i18n';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

export default function MyApp({
  Component,
  pageProps,
}: AppProps<{ session: Session }>) {
  return (
    <SessionProvider session={pageProps.session}>
      <QueryClientProvider client={queryClient}>
        <I18nProvider>
          <AdminLayout>
            <Component {...pageProps} />
          </AdminLayout>
        </I18nProvider>
      </QueryClientProvider>
    </SessionProvider>
  );
}
