import React, { useEffect, useState } from 'react';

interface Summary {
  conversions: number;
  impressions: number;
}

export function AbTestSummary({ abTestId }: { abTestId: number }) {
  const [summary, setSummary] = useState<Summary | null>(null);

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
    return <div data-testid="abtest-loading">Loading...</div>;
  }
  return (
    <div data-testid="abtest-summary">
      Conversions: {summary.conversions} / Impressions: {summary.impressions}
    </div>
  );
}
