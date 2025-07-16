import React from 'react';
import { useTranslation } from 'react-i18next';

export default function AbTestsPage() {
  const { t } = useTranslation();
  return <div>{t('abTestsPlaceholder')}</div>;
}
