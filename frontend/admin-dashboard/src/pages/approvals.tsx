// @flow
import React from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import dynamic from 'next/dynamic';
import { useTranslation } from 'react-i18next';
import { useQueryClient } from '@tanstack/react-query';
import { usePendingRuns } from '../lib/trpc/hooks';
import { trpc } from '../trpc';

const Button = dynamic(() => import('../components/Button'));

function ApprovalsPage() {
  const { t } = useTranslation();
  const { data: runs, isLoading } = usePendingRuns();
  const queryClient = useQueryClient();

  const removeRun = (id: string) => {
    queryClient.setQueryData<string[] | undefined>(['pendingRuns'], (old) =>
      old?.filter((r) => r !== id)
    );
  };

  const approve = async (runId: string) => {
    removeRun(runId);
    try {
      await trpc.approvals.approve(runId);
    } catch {
      await queryClient.invalidateQueries({ queryKey: ['pendingRuns'] });
      alert(t('approvalFailed'));
    }
  };

  const reject = async (runId: string) => {
    removeRun(runId);
    try {
      await trpc.approvals.reject(runId);
    } catch {
      await queryClient.invalidateQueries({ queryKey: ['pendingRuns'] });
      alert(t('rejectionFailed'));
    }
  };

  return (
    <div className="space-y-2">
      <h1>{t('approvals')}</h1>
      {isLoading || !runs ? (
        <div>{t('loading')}</div>
      ) : runs.length === 0 ? (
        <div>{t('noPendingRuns')}</div>
      ) : (
        <ul>
          {runs.map((id) => (
            <li key={id} className="space-x-2">
              <span>{id}</span>
              <Button onClick={() => approve(id)} ariaLabel={t('approve')}>
                {t('approve')}
              </Button>
              <Button
                onClick={() => reject(id)}
                ariaLabel={t('reject')}
                className="bg-red-600"
              >
                {t('reject')}
              </Button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default withPageAuthRequired(ApprovalsPage);
