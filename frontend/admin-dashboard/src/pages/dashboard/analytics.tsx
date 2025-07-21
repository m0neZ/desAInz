// @flow
import React from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { useAnalyticsSummary } from '../../lib/trpc/hooks';

function AnalyticsPage() {
  const { t } = useTranslation();
  const { data, isLoading } = useAnalyticsSummary();

  if (isLoading || !data) {
    return <div>{t('loading')}</div>;
  }
  return (
    <div>
      <h1>{t('analytics')}</h1>
      <div>
        Revenue: {data.revenue.toFixed(2)} / Conversions: {data.conversions}
      </div>
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => ({
  props: {},
  revalidate: 60,
});
export default withPageAuthRequired(AnalyticsPage);
