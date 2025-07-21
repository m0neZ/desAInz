// @flow
import React from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { useAnalyticsSummary } from '../../lib/trpc/hooks';
import dynamic from 'next/dynamic';

const AnalyticsChart = dynamic(() => import('../../components/AnalyticsChart'), {
  ssr: false,
});
const LatencyChart = dynamic(() => import('../../components/LatencyChart'), {
  ssr: false,
});

function AnalyticsPage() {
  const { t } = useTranslation();
  const { data, isLoading } = useAnalyticsSummary();

  if (isLoading || !data) {
    return <div>{t('loading')}</div>;
  }
  return (
    <div className="space-y-4">
      <h1>{t('analytics')}</h1>
      <div>
        Revenue: {data.revenue.toFixed(2)} / Conversions: {data.conversions}
      </div>
      <AnalyticsChart />
      <LatencyChart />
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => ({
  props: {},
  revalidate: 60,
});
export default withPageAuthRequired(AnalyticsPage);
