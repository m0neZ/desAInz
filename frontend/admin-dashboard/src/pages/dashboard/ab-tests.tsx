import React from 'react';
import dynamic from 'next/dynamic';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';

const AbTestSummary = dynamic(() => import('../../components/AbTestSummary'), {
  ssr: false,
});

export default function AbTestsPage() {
  const { t } = useTranslation();
  return (
    <div>
      <h1>{t('abTests')}</h1>
      <AbTestSummary abTestId={1} />
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => {
  return {
    props: {},
    revalidate: 60,
  };
};
