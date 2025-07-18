import React, { useEffect, useState } from 'react';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { trpc, type AnalyticsData } from '../../trpc';

export default function AnalyticsPage() {
  const { t } = useTranslation();
  const [data, setData] = useState<AnalyticsData | null>(null);

  useEffect(() => {
    async function load() {
      setData(await trpc.analytics.summary());
    }
    void load();
  }, []);

  if (!data) {
    return <div>Loading...</div>;
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
