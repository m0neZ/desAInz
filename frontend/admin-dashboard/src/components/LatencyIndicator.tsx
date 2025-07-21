// @flow
import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

export default function LatencyIndicator() {
  const [hours, setHours] = useState<number | null>(null);
  const { t } = useTranslation();
  const base =
    process.env.NEXT_PUBLIC_MONITORING_URL ?? 'http://localhost:8000';
  useEffect(() => {
    async function fetchLatency() {
      try {
        const res = await fetch(`${base}/latency`);
        if (res.ok) {
          const data = await res.json();
          setHours(data.average_seconds / 3600);
        }
      } catch {
        /* ignore */
      }
    }
    void fetchLatency();
    const id = setInterval(fetchLatency, 5000);
    return () => clearInterval(id);
  }, [base]);

  if (hours === null) {
    return <div>{t('loading')}</div>;
  }
  return (
    <div data-testid="latency-indicator">
      {t('latency', { hours: hours.toFixed(2) })}
    </div>
  );
}
