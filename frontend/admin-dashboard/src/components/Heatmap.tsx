// @flow
import React from 'react';
import { useHeatmap } from '../lib/trpc/hooks';

/**
 * Display heatmap entries using the ``useHeatmap`` hook.
 */
export function Heatmap() {
  const { data, isLoading } = useHeatmap();

  if (isLoading || !data) {
    return <div data-testid="heatmap-loading">Loading...</div>;
  }
  return (
    <ul data-testid="heatmap">
      {data.map((entry) => (
        <li key={entry.label}>{`${entry.label}: ${entry.count}`}</li>
      ))}
    </ul>
  );
}
