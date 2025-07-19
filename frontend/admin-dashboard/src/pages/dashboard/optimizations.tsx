import React, { useEffect, useState } from 'react';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { trpc } from '../../trpc';

export default function OptimizationsPage() {
  const { t } = useTranslation();
  const [items, setItems] = useState<string[]>([]);

  useEffect(() => {
    async function load() {
      try {
        setItems(await trpc.optimizations.list());
      } catch {
        setItems([]);
      }
    }
    void load();
  }, []);

  return (
    <div className="space-y-2">
      <h1>{t('optimizations')}</h1>
      <ul>
        {items.map((opt, idx) => (
          <li key={idx}>{opt}</li>
        ))}
      </ul>
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => ({
  props: {},
  revalidate: 60,
});
