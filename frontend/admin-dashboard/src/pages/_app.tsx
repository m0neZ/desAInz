import type { AppProps } from 'next/app';
import '../styles/globals.css';
import dynamic from 'next/dynamic';

const AdminLayout = dynamic(() => import('../layouts/AdminLayout'));

export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <AdminLayout>
      <Component {...pageProps} />
    </AdminLayout>
  );
}
