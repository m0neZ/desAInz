import React from 'react';
import { useTranslation } from 'react-i18next';

export default function GalleryPage() {
  const { t } = useTranslation();
  return <div>{t('galleryPlaceholder')}</div>;
}

export async function getStaticProps() {
  return { props: {}, revalidate: 60 };
}
