import React from 'react';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { useMetrics } from '../../lib/trpc/hooks';

export default function MetricsPage() {
  const { t } = useTranslation();
  const { data: metrics, isLoading } = useMetrics();

  return (
    <div className="space-y-2">
      <h1>{t('metrics')}</h1>
      {isLoading || !metrics ? <div>{t('loading')}</div> : <pre>{metrics}</pre>}
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => ({
  props: {},
  revalidate: 60,
});
