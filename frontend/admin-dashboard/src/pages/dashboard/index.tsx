import React from 'react';
import { useTranslation } from 'react-i18next';
import StatusIndicator from '../../components/StatusIndicator';
import LatencyIndicator from '../../components/LatencyIndicator';

export default function DashboardPage() {
  const { t } = useTranslation();
  return (
    <div className="space-y-4">
      <StatusIndicator />
      <LatencyIndicator />
      <div>{t('signalStreamComingSoon')}</div>
    </div>
  );
}
