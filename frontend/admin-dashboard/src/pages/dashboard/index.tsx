import React from 'react';
import dynamic from 'next/dynamic';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { useSignals } from '../../lib/trpc/hooks';

const StatusIndicator = dynamic(
  () => import('../../components/StatusIndicator')
);
const LatencyIndicator = dynamic(
  () => import('../../components/LatencyIndicator')
);
const TrendingKeywords = dynamic(
  () => import('../../components/TrendingKeywords'),
  { ssr: false }
);
const AbTestSummary = dynamic(() => import('../../components/AbTestSummary'), {
  ssr: false,
});

export default function DashboardPage() {
  const { t } = useTranslation();
  const { data: signals, isLoading } = useSignals();

  return (
    <div className="space-y-4">
      <StatusIndicator />
      <LatencyIndicator />
      <TrendingKeywords />
      <AbTestSummary abTestId={1} />
      <h1>{t('signalStream')}</h1>
      {isLoading || !signals ? (
        <div>{t('loading')}</div>
      ) : (
        <ul>
          {signals.map((s) => (
            <li key={s.id}>
              {s.source}: {s.content}
            </li>
          ))}
        </ul>
      )}
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
