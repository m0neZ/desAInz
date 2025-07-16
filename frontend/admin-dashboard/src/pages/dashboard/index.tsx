import React from 'react';
import { useTranslation } from 'react-i18next';
import StatusIndicator from '../../components/StatusIndicator';

export default function DashboardPage() {
  const { t } = useTranslation();
  return (
    <div className="space-y-4">
      <StatusIndicator />
      <div>{t('signalStreamComingSoon')}</div>
    </div>
  );
}
