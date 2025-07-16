import React from 'react';
import dynamic from 'next/dynamic';
import { useTranslation } from 'react-i18next';

// Load the potentially heavy summary component lazily
const AbTestSummary = dynamic(
  () => import('../../components/AbTestSummary').then((m) => m.AbTestSummary),
  { ssr: false, loading: () => <div>Loading...</div> }
);

export default function AbTestsPage() {
  const { t } = useTranslation();
  return (
    <div>
      <h1>{t('abTests')}</h1>
      <AbTestSummary abTestId={1} />
    </div>
  );
}

export async function getStaticProps() {
  return { props: {}, revalidate: 60 };
}
