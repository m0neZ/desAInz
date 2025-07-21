'use client';
import { useEffect, useState } from 'react';
import { trpc, type AnalyticsData } from '../../src/trpc';
import { AnalyticsChart } from '../../src/components/AnalyticsChart';
import { LatencyChart } from '../../src/components/LatencyChart';
import { AlertStatusIndicator } from '../../src/components/AlertStatusIndicator';

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<AnalyticsData | null>(null);

  useEffect(() => {
    async function load() {
      setMetrics(await trpc.analytics.summary());
    }
    void load();
  }, []);

  return (
    <div className="space-y-4">
      <h1>Metrics</h1>
      {metrics ? (
        <>
          <p>Revenue: {metrics.revenue}</p>
          <p>Conversions: {metrics.conversions}</p>
        </>
      ) : (
        <div>Loading...</div>
      )}
      <AlertStatusIndicator />
      <AnalyticsChart />
      <LatencyChart />
    </div>
  );
}
