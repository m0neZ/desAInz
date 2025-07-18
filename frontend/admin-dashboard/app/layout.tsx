import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import '../src/styles/globals.css';
import { LanguageSwitcher } from '../src/components/LanguageSwitcher';
import i18n from '../src/i18n';

export const metadata: Metadata = {
  title: 'Admin Dashboard',
  description: 'Admin dashboard application',
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html lang={i18n.language}>
      <body>
        <div className="p-2">
          <LanguageSwitcher />
        </div>
        {children}
      </body>
    </html>
  );
}
