import React from 'react';
import Link from 'next/link';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
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
          <Link href="/dashboard/ab-tests" className="block hover:underline">
            AB Tests
          </Link>
        </nav>
      </aside>
      <div className="flex flex-col flex-1">
        <header className="bg-gray-100 p-4 shadow">Admin Dashboard</header>
        <main className="p-4 flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
