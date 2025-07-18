import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { trpc, type AnalyticsData } from '../../../src/trpc';

export default function MetricsPage() {
  const { t } = useTranslation();
  const [metrics, setMetrics] = useState<AnalyticsData | null>(null);

  useEffect(() => {
    async function load() {
      setMetrics(await trpc.analytics.summary());
    }
    void load();
  }, []);

  if (!metrics) {
    return <div>{t('loading')}</div>;
  }

  return (
    <div className="space-y-2">
      <h1>{t('metrics')}</h1>
      <p>
        {t('revenue')}: {metrics.revenue}
      </p>
      <p>
        {t('conversions')}: {metrics.conversions}
      </p>
    </div>
  );
}
