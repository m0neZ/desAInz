// @flow
import React from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { useOptimizationRecommendations } from '../../lib/trpc/hooks';

function OptimizationRecommendationsPage() {
  const { t } = useTranslation();
  const { data: recs, isLoading } = useOptimizationRecommendations();

  return (
    <div className="space-y-2">
      <h1>{t('optimizationRecommendations')}</h1>
      {isLoading || !recs ? (
        <div>{t('loading')}</div>
      ) : (
        <ul>
          {recs.map((r, idx) => (
            <li key={idx}>{r}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => ({
  props: {},
  revalidate: 60,
});
export default withPageAuthRequired(OptimizationRecommendationsPage);
