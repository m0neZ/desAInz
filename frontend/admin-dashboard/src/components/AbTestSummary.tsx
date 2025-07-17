import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

interface Summary {
  conversions: number;
  impressions: number;
}

export function AbTestSummary({ abTestId }: { abTestId: number }) {
  const [summary, setSummary] = useState<Summary | null>(null);
  const { t } = useTranslation();

  useEffect(() => {
    async function load() {
      const res = await fetch(`/api/analytics/ab_test_results/${abTestId}`);
      if (res.ok) {
        setSummary(await res.json());
      }
    }
    void load();
  }, [abTestId]);

  if (!summary) {
    return <div data-testid="abtest-loading">{t('loading')}</div>;
  }
  return (
    <div data-testid="abtest-summary">
      {t('summary', {
        conversions: summary.conversions,
        impressions: summary.impressions,
      })}
    </div>
  );
}
