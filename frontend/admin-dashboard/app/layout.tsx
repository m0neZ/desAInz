import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import '../src/styles/globals.css';
import { LanguageSwitcher } from '../src/components/LanguageSwitcher';
import { I18nProvider } from '../src/i18n';

export const metadata: Metadata = {
  title: 'Admin Dashboard',
  description: 'Admin dashboard application',
  manifest: '/manifest.json',
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <I18nProvider>
          <div className="p-2">
            <LanguageSwitcher />
          </div>
          {children}
        </I18nProvider>
      </body>
    </html>
  );
}
