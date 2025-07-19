import React, { useEffect, useState } from 'react';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { trpc } from '../../trpc';

export default function MetricsPage() {
  const { t } = useTranslation();
  const [metrics, setMetrics] = useState('');

  useEffect(() => {
    async function load() {
      try {
        setMetrics(await trpc.metrics.list());
      } catch {
        setMetrics('');
      }
    }
    void load();
  }, []);

  return (
    <div className="space-y-2">
      <h1>{t('metrics')}</h1>
      <pre>{metrics}</pre>
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => ({
  props: {},
  revalidate: 60,
});
