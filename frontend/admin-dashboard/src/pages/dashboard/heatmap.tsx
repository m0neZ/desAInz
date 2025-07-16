import React from 'react';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';

export default function HeatmapPage() {
  const { t } = useTranslation();
  return <div>{t('heatmapPlaceholder')}</div>;
}

export const getStaticProps: GetStaticProps = async () => {
  return {
    props: {},
    revalidate: 60,
  };
};
