// @flow
import React from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { useOptimizations } from '../../lib/trpc/hooks';

function OptimizationsPage() {
  const { t } = useTranslation();
  const { data: items, isLoading } = useOptimizations();

  return (
    <div className="space-y-2">
      <h1>{t('optimizations')}</h1>
      {isLoading || !items ? (
        <div>{t('loading')}</div>
      ) : (
        <ul>
          {items.map((opt, idx) => (
            <li key={idx}>{opt}</li>
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
export default withPageAuthRequired(OptimizationsPage);
