import React from 'react';
import dynamic from 'next/dynamic';
import { useTranslation } from 'react-i18next';

// Dynamically import the status indicator to split the bundle
const StatusIndicator = dynamic(
  () => import('../../components/StatusIndicator'),
  { ssr: false, loading: () => <div>Loading...</div> }
);

export default function DashboardPage() {
  const { t } = useTranslation();
  return (
    <div className="space-y-4">
      <StatusIndicator />
      <div>{t('signalStreamComingSoon')}</div>
    </div>
  );
}

export async function getStaticProps() {
  return { props: {}, revalidate: 60 };
}
