import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import '../src/styles/globals.css';

export const metadata: Metadata = {
  title: 'Admin Dashboard',
  description: 'Admin dashboard application',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <a href="#root-main" className="skip-link">
          Skip to main content
        </a>
        <main id="root-main">{children}</main>
      </body>
    </html>
  );
}
