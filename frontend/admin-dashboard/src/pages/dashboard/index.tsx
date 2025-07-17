import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { trpc, type Signal } from '../../../../../src/trpc';

const StatusIndicator = dynamic(
  () => import('../../components/StatusIndicator')
);
const LatencyIndicator = dynamic(
  () => import('../../components/LatencyIndicator')
);

export default function DashboardPage() {
  const { t } = useTranslation();
  const [signals, setSignals] = useState<Signal[]>([]);

  useEffect(() => {
    async function load() {
      setSignals(await trpc.signals.list());
    }
    void load();
  }, []);

  return (
    <div className="space-y-4">
      <StatusIndicator />
      <LatencyIndicator />
      <h1>{t('signalStream')}</h1>
      <ul>
        {signals.map((s) => (
          <li key={s.id}>
            {s.source}: {s.content}
          </li>
        ))}
      </ul>
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => {
  return {
    props: {},
    // Revalidate every 60 seconds to enable incremental static regeneration
    revalidate: 60,
  };
};
