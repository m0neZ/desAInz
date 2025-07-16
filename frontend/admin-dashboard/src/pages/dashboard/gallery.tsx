import React from 'react';
import { useTranslation } from 'react-i18next';

export default function GalleryPage() {
  const { t } = useTranslation();
  return <div>{t('galleryPlaceholder')}</div>;
}
