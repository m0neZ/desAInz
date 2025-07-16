import React from 'react';
import { useTranslation } from 'react-i18next';

export default function DashboardPage() {
  const { t } = useTranslation();
  return <div>{t('signalStreamComingSoon')}</div>;
}
