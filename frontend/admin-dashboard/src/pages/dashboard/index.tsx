import React from 'react';
import dynamic from 'next/dynamic';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';

const StatusIndicator = dynamic(
  () => import('../../components/StatusIndicator')
);
const LatencyIndicator = dynamic(
  () => import('../../components/LatencyIndicator')
);

export default function DashboardPage() {
  const { t } = useTranslation();
  return (
    <div className="space-y-4">
      <StatusIndicator />
      <LatencyIndicator />
      <div>{t('signalStreamComingSoon')}</div>
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => {
  return {
    props: {},
    // Revalidate every 60 seconds to enable incremental static regeneration
    revalidate: 60,
  };
};
