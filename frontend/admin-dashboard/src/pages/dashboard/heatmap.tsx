import React, { useEffect, useState } from 'react';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { trpc, type HeatmapEntry } from '../../../../../src/trpc';

export default function HeatmapPage() {
  const { t } = useTranslation();
  const [data, setData] = useState<HeatmapEntry[]>([]);

  useEffect(() => {
    async function load() {
      setData(await trpc.heatmap.list());
    }
    void load();
  }, []);

  return (
    <div>
      <h1>{t('heatmap')}</h1>
      <ul>
        {data.map((entry) => (
          <li key={entry.label}>
            {entry.label}: {entry.count}
          </li>
        ))}
      </ul>
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => {
  return {
    props: {},
    revalidate: 60,
  };
};
