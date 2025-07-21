import React from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { useHeatmap } from '../../lib/trpc/hooks';

function HeatmapPage() {
  const { t } = useTranslation();
  const { data, isLoading } = useHeatmap();

  return (
    <div>
      <h1>{t('heatmap')}</h1>
      {isLoading || !data ? (
        <div>{t('loading')}</div>
      ) : (
        <ul>
          {data.map((entry) => (
            <li key={entry.label}>
              {entry.label}: {entry.count}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => {
  return {
    props: {},
    revalidate: 60,
  };
};
export default withPageAuthRequired(HeatmapPage);
