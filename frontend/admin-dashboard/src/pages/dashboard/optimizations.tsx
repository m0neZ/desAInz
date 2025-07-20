import React from 'react';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { useOptimizations } from '../../lib/trpc/hooks';

export default function OptimizationsPage() {
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
