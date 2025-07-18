import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { trpc, type AnalyticsData } from '../../src/trpc';
import { AnalyticsChart } from '../../src/components/AnalyticsChart';
import { LatencyChart } from '../../src/components/LatencyChart';
import { AlertStatusIndicator } from '../../src/components/AlertStatusIndicator';

export default function MetricsPage() {
  const { t } = useTranslation();
  const [metrics, setMetrics] = useState<AnalyticsData | null>(null);

  useEffect(() => {
    async function load() {
      setMetrics(await trpc.analytics.summary());
    }
    void load();
  }, []);

  return (
    <div className="space-y-4">
      <h1>{t('metrics')}</h1>
      {metrics ? (
        <>
          <p>
            {t('revenue')}: {metrics.revenue}
          </p>
          <p>
            {t('conversions')}: {metrics.conversions}
          </p>
        </>
      ) : (
        <div>{t('loading')}</div>
      )}
      <AlertStatusIndicator />
      <AnalyticsChart />
      <LatencyChart />
    </div>
  );
}
