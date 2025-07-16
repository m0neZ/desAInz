import dynamic from 'next/dynamic';
import React from 'react';

const Dashboard = dynamic(() => import('../../features/Dashboard'));

export default function DashboardPage() {
  return <Dashboard />;
}
