import React from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import dynamic from 'next/dynamic';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';

const AbTestSummary = dynamic(() => import('../../components/AbTestSummary'), {
  ssr: false,
});

function AbTestsPage() {
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
export default withPageAuthRequired(AbTestsPage);
