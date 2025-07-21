// @flow
import React from 'react';
import { useTrendingKeywords } from '../lib/trpc/hooks';

export function TrendingKeywords({ limit }: { limit?: number }) {
  const { data, isLoading } = useTrendingKeywords(limit);

  if (isLoading || !data) {
    return <div data-testid="trending-loading">Loading...</div>;
  }
  return (
    <div data-testid="trending-keywords">
      <h2>Trending Keywords</h2>
      <ul>
        {data.map((kw, idx) => (
          <li key={kw}>
            {idx + 1}. {kw}
          </li>
        ))}
      </ul>
    </div>
  );
}
