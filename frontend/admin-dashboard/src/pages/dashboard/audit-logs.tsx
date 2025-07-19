import React, { useEffect, useState } from 'react';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { trpc, type AuditLog } from '../../trpc';

export default function AuditLogsPage() {
  const { t } = useTranslation();
  const [logs, setLogs] = useState<AuditLog[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const result = await trpc.auditLogs.list();
        setLogs(result.items);
      } catch {
        setLogs([]);
      }
    }
    void load();
  }, []);

  return (
    <div className="space-y-2">
      <h1>{t('auditLogs')}</h1>
      <ul>
        {logs.map((log) => (
          <li
            key={log.id}
          >{`${log.timestamp} ${log.username} ${log.action}`}</li>
        ))}
      </ul>
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => ({
  props: {},
  revalidate: 60,
});
