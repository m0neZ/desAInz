// @flow
import React from 'react';
import { useTranslation } from 'react-i18next';
import { useTrendingKeywords } from '../lib/trpc/hooks';

export function TrendingKeywords({ limit }: { limit?: number }) {
  const { t } = useTranslation();
  const { data, isLoading } = useTrendingKeywords(limit);

  if (isLoading || !data) {
    return <div data-testid="trending-loading">{t('loading')}</div>;
  }
  return (
    <div data-testid="trending-keywords">
      <h2>{t('trendingKeywords')}</h2>
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
