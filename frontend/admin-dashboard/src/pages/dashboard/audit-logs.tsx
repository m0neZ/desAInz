import React from 'react';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { useAuditLogs } from '../../lib/trpc/hooks';

export default function AuditLogsPage() {
  const { t } = useTranslation();
  const { data, isLoading } = useAuditLogs();

  return (
    <div className="space-y-2">
      <h1>{t('auditLogs')}</h1>
      {isLoading || !data ? (
        <div>{t('loading')}</div>
      ) : (
        <ul>
          {data.items.map((log) => (
            <li
              key={log.id}
            >{`${log.timestamp} ${log.username} ${log.action}`}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => ({
  props: {},
  revalidate: 60,
});
