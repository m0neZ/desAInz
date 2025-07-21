import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import '../src/styles/globals.css';

export const metadata: Metadata = {
  title: 'Admin Dashboard',
  description: 'Admin dashboard application',
  manifest: '/manifest.json',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
