// @flow
import React from 'react';
import { useTranslation } from 'react-i18next';
import { useAbTestSummary } from '../lib/trpc/hooks';

export function AbTestSummary({ abTestId }: { abTestId: number }) {
  const { t } = useTranslation();
  const { data, isLoading } = useAbTestSummary(abTestId);

  if (isLoading || !data) {
    return <div data-testid="abtest-loading">{t('loading')}</div>;
  }
  return (
    <div data-testid="abtest-summary">
      {t('summary', {
        conversions: data.conversions,
        impressions: data.impressions,
      })}
    </div>
  );
}
