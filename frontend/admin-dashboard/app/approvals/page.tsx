'use client';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '../../src/components/Button';
import { trpc } from '../../src/trpc';

export default function ApprovalsPage() {
  const { t } = useTranslation();
  const [runId, setRunId] = useState('');
  const [status, setStatus] = useState('');

  async function approve() {
    try {
      await trpc.approvals.approve(runId);
      setStatus(t('approved'));
    } catch {
      setStatus(t('approvalFailed'));
    }
  }

  return (
    <div className="space-y-2">
      <h1>{t('approvals')}</h1>
      <input
        className="border p-2"
        value={runId}
        onChange={(e) => setRunId(e.target.value)}
        placeholder={t('runId') ?? ''}
      />
      <Button onClick={approve}>{t('approve')}</Button>
      {status && <p>{status}</p>}
    </div>
  );
}
