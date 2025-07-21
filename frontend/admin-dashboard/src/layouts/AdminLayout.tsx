// @flow
import React from 'react';
import Link from 'next/link';
import AuthButton from '../components/AuthButton';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const t = (s: string) => s;
  return (
    <div className="flex h-screen">
      <aside className="w-64 bg-gray-800 text-white p-4">
        <nav className="space-y-2">
          <Link href="/dashboard" className="block hover:underline">
            Dashboard
          </Link>
          <Link href="/dashboard/heatmap" className="block hover:underline">
            Heatmap
          </Link>
          <Link href="/dashboard/gallery" className="block hover:underline">
            Gallery
          </Link>
          <Link href="/dashboard/publish" className="block hover:underline">
            Publish Tasks
          </Link>
          <Link
            href="/dashboard/low-performers"
            className="block hover:underline"
          >
            Low Performing Listings
          </Link>
          <Link href="/dashboard/ab-tests" className="block hover:underline">
            AB Tests
          </Link>
          <Link href="/dashboard/analytics" className="block hover:underline">
            Analytics
          </Link>
          <Link href="/dashboard/roles" className="block hover:underline">
            Roles
          </Link>
          <Link href="/dashboard/audit-logs" className="block hover:underline">
            Audit Logs
          </Link>
          <Link
            href="/dashboard/optimizations"
            className="block hover:underline"
          >
            Optimizations
          </Link>
          <Link href="/dashboard/metrics" className="block hover:underline">
            Metrics
          </Link>
          <Link href="/approvals" className="block hover:underline">
            Approvals
          </Link>
          {process.env.NEXT_PUBLIC_ENABLE_ZAZZLE === 'true' && (
            <Link href="/dashboard/zazzle" className="block hover:underline">
              Zazzle
            </Link>
          )}
          <Link href="/dashboard/preferences" className="block hover:underline">
            Preferences
          </Link>
          <Link href="/dashboard/maintenance" className="block hover:underline">
            Maintenance
          </Link>
        </nav>
      </aside>
      <div className="flex flex-col flex-1">
        <header className="bg-gray-100 p-4 shadow flex items-center space-x-4">
          <span className="flex-1">Admin Dashboard</span>
          <AuthButton />
        </header>
        <main className="p-4 flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
