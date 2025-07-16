import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '../../components/Button';

export default function MaintenancePage() {
  const { t } = useTranslation();
  const [status, setStatus] = useState('');

  const runCleanup = async () => {
    const resp = await fetch('/maintenance/cleanup', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + localStorage.getItem('token') },
    });
    if (resp.ok) {
      setStatus(t('cleanupTriggered'));
    } else {
      setStatus(t('cleanupFailed'));
    }
  };

  return (
    <div className="space-y-2">
      <Button onClick={runCleanup}>{t('runCleanup')}</Button>
      {status && <div>{status}</div>}
    </div>
  );
}
