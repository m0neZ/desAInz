'use client';
import { useTranslation } from 'react-i18next';
import { useQueryClient } from '@tanstack/react-query';
import { Button } from '../../src/components/Button';
import { trpc } from '../../src/trpc';
import { usePendingRuns } from '../../src/lib/trpc/hooks';

export default function ApprovalsPage() {
  const { t } = useTranslation();
  const { data: runs, isLoading } = usePendingRuns();
  const queryClient = useQueryClient();

  const removeRun = (id: string) => {
    queryClient.setQueryData<string[] | undefined>(['pendingRuns'], (old) =>
      old?.filter((r) => r !== id)
    );
  };

  async function approve(id: string) {
    removeRun(id);
    try {
      await trpc.approvals.approve(id);
    } catch {
      await queryClient.invalidateQueries({ queryKey: ['pendingRuns'] });
      alert(t('approvalFailed'));
    }
  }

  async function reject(id: string) {
    removeRun(id);
    try {
      await trpc.approvals.reject(id);
    } catch {
      await queryClient.invalidateQueries({ queryKey: ['pendingRuns'] });
      alert(t('rejectionFailed'));
    }
  }

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
