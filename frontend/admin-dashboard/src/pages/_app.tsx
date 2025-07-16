import type { AppProps } from 'next/app';
import '../styles/globals.css';
import AdminLayout from '../layouts/AdminLayout';

export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <AdminLayout>
      <Component {...pageProps} />
    </AdminLayout>
  );
}
