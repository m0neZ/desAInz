import type { AppProps } from 'next/app';
import type { Session } from 'next-auth';
import { SessionProvider } from 'next-auth/react';
import '../styles/globals.css';
import AdminLayout from '../layouts/AdminLayout';
import '../i18n';

export default function MyApp({
  Component,
  pageProps,
}: AppProps<{ session: Session }>) {
  return (
    <SessionProvider session={pageProps.session}>
      <AdminLayout>
        <Component {...pageProps} />
      </AdminLayout>
    </SessionProvider>
  );
}
