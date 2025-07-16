import React from 'react';
import Link from 'next/link';
import { useTranslation } from 'react-i18next';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { t } = useTranslation();
  return (
    <div className="flex h-screen">
      <aside className="w-64 bg-gray-800 text-white p-4">
        <nav className="space-y-2">
          <Link href="/dashboard" className="block hover:underline">
            {t('dashboard')}
          </Link>
          <Link href="/dashboard/heatmap" className="block hover:underline">
            {t('heatmap')}
          </Link>
          <Link href="/dashboard/gallery" className="block hover:underline">
            {t('gallery')}
          </Link>
          <Link href="/dashboard/publish" className="block hover:underline">
            {t('updateAndPublish')}
          </Link>
          <Link href="/dashboard/low-performers" className="block hover:underline">
            {t('lowPerformers')}
          </Link>
          <Link href="/dashboard/ab-tests" className="block hover:underline">
            {t('abTests')}
          </Link>
          <Link href="/dashboard/roles" className="block hover:underline">
            {t('roles')}
          </Link>
          <Link href="/dashboard/preferences" className="block hover:underline">
            {t('preferences')}
          </Link>
          <Link href="/dashboard/maintenance" className="block hover:underline">
            {t('maintenance')}
          </Link>
        </nav>
      </aside>
      <div className="flex flex-col flex-1">
        <header className="bg-gray-100 p-4 shadow">{t('title')}</header>
        <main className="p-4 flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
