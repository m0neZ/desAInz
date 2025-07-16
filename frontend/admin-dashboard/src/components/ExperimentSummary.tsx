/**
 * Display A/B test results.
 */
import React, { useEffect, useState } from 'react';

export interface TestResult {
  ab_test_id: number;
  impressions: number;
  conversions: number;
}

export function ExperimentSummary() {
  const [data, setData] = useState<TestResult[]>([]);
  useEffect(() => {
    fetch('/analytics/ab-tests')
      .then((r) => r.json())
      .then(setData)
      .catch(() => {});
  }, []);
  return (
    <div>
      <h2 className="text-lg font-bold mb-2">Experiment Outcomes</h2>
      <ul>
        {data.map((row) => (
          <li key={row.ab_test_id}>
            Test {row.ab_test_id}: {row.conversions}/{row.impressions}
          </li>
        ))}
      </ul>
    </div>
  );
}
