// @flow
import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { AnimatePresence, motion } from 'framer-motion';
import AuthButton from '../components/AuthButton';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  return (
    <div className="flex h-screen">
      <aside className="w-48 md:w-64 bg-gray-800 text-white p-2 md:p-4">
        <nav className="space-y-2">
          <Link
            href="/dashboard"
            className="block hover:underline focus:outline-none focus:ring"
            aria-label="Dashboard"
          >
            Dashboard
          </Link>
          <Link
            href="/dashboard/heatmap"
            className="block hover:underline focus:outline-none focus:ring"
            aria-label="Heatmap"
          >
            Heatmap
          </Link>
          <Link
            href="/dashboard/gallery"
            className="block hover:underline focus:outline-none focus:ring"
            aria-label="Gallery"
          >
            Gallery
          </Link>
          <Link
            href="/dashboard/publish"
            className="block hover:underline focus:outline-none focus:ring"
            aria-label="Publish Tasks"
          >
            Publish Tasks
          </Link>
          <Link
            href="/dashboard/low-performers"
            className="block hover:underline focus:outline-none focus:ring"
            aria-label="Low Performing Listings"
          >
            Low Performing Listings
          </Link>
          <Link
            href="/dashboard/ab-tests"
            className="block hover:underline focus:outline-none focus:ring"
            aria-label="AB Tests"
          >
            AB Tests
          </Link>
          <Link
            href="/dashboard/analytics"
            className="block hover:underline focus:outline-none focus:ring"
            aria-label="Analytics"
          >
            Analytics
          </Link>
          <Link
            href="/dashboard/roles"
            className="block hover:underline focus:outline-none focus:ring"
            aria-label="Roles"
          >
            Roles
          </Link>
          <Link
            href="/dashboard/audit-logs"
            className="block hover:underline focus:outline-none focus:ring"
            aria-label="Audit Logs"
          >
            Audit Logs
          </Link>
          <Link
            href="/dashboard/optimizations"
            className="block hover:underline focus:outline-none focus:ring"
            aria-label="Optimizations"
          >
            Optimizations
          </Link>
          <Link
            href="/dashboard/metrics"
            className="block hover:underline focus:outline-none focus:ring"
            aria-label="Metrics"
          >
            Metrics
          </Link>
          <Link
            href="/approvals"
            className="block hover:underline focus:outline-none focus:ring"
            aria-label="Approvals"
          >
            Approvals
          </Link>
          {process.env.NEXT_PUBLIC_ENABLE_ZAZZLE === 'true' && (
            <Link
              href="/dashboard/zazzle"
              className="block hover:underline focus:outline-none focus:ring"
              aria-label="Zazzle"
            >
              Zazzle
            </Link>
          )}
          <Link
            href="/dashboard/preferences"
            className="block hover:underline focus:outline-none focus:ring"
            aria-label="Preferences"
          >
            Preferences
          </Link>
          <Link
            href="/dashboard/maintenance"
            className="block hover:underline focus:outline-none focus:ring"
            aria-label="Maintenance"
          >
            Maintenance
          </Link>
        </nav>
      </aside>
      <div className="flex flex-col flex-1">
        <header className="bg-gray-100 p-2 md:p-4 shadow flex items-center space-x-4">
          <span className="flex-1">Admin Dashboard</span>
          <AuthButton />
        </header>
        <AnimatePresence mode="wait">
          <motion.main
            key={router.asPath}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="p-2 md:p-4 flex-1 overflow-auto"
          >
            {children}
          </motion.main>
        </AnimatePresence>
      </div>
    </div>
  );
}
