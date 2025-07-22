// @flow
import React from 'react';
import { useAbTestSummary } from '../lib/trpc/hooks';

/**
 * Display conversion statistics for the given A/B test.
 *
 * Fetches data using ``useAbTestSummary`` and shows loading state while
 * waiting for the results.
 */

export function AbTestSummary({ abTestId }: { abTestId: number }) {
  const { data, isLoading } = useAbTestSummary(abTestId);

  if (isLoading || !data) {
    return <div data-testid="abtest-loading">Loading...</div>;
  }
  return (
    <div data-testid="abtest-summary">
      {`Conversions: ${data.conversions} / Impressions: ${data.impressions}`}
    </div>
  );
}
