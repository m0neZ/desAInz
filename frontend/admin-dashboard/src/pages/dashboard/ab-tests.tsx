import React from 'react';
import { useTranslation } from 'react-i18next';
import { AbTestSummary } from '../../components/AbTestSummary';

export default function AbTestsPage() {
  const { t } = useTranslation();
  return (
    <div>
      <h1>{t('abTests')}</h1>
      <AbTestSummary abTestId={1} />
    </div>
  );
}
