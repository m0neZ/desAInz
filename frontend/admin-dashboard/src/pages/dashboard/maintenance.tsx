// @flow
import React, { useState } from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import { useTranslation } from 'react-i18next';
import dynamic from 'next/dynamic';
import { fetchWithAuth } from '../../hooks/useAuthFetch';

const Button = dynamic(() => import('../../components/Button'));

function MaintenancePage() {
  const { t } = useTranslation();
  const [status, setStatus] = useState('');

  const runCleanup = async () => {
    const resp = await fetchWithAuth('/maintenance/cleanup', {
      method: 'POST',
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
export default withPageAuthRequired(MaintenancePage);
