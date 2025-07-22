// @flow
import React from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import dynamic from 'next/dynamic';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { useMetricsSummary } from '../../lib/trpc/hooks';

const AnalyticsChart = dynamic(
  () => import('../../components/AnalyticsChart'),
  {
    ssr: false,
  }
);
const LatencyChart = dynamic(() => import('../../components/LatencyChart'), {
  ssr: false,
});

function MetricsChartsPage() {
  const { t } = useTranslation();
  const { data, isLoading } = useMetricsSummary();

  return (
    <div className="space-y-4">
      <h1>{t('metricsCharts')}</h1>
      {isLoading || !data ? (
        <div>{t('loading')}</div>
      ) : (
        <div className="space-y-2">
          <pre>{JSON.stringify(data, null, 2)}</pre>
          <AnalyticsChart />
          <LatencyChart />
        </div>
      )}
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => ({
  props: {},
  revalidate: 60,
});
export default withPageAuthRequired(MetricsChartsPage);
