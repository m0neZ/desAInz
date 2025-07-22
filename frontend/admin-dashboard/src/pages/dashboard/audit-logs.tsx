// @flow
import React from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { useAuditLogs } from '../../lib/trpc/hooks';
import { useState } from 'react';

function AuditLogsPage() {
  const { t } = useTranslation();
  const [page, setPage] = useState(0);
  const limit = 50;
  const { data, isLoading } = useAuditLogs(limit, page);

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
      <div className="space-x-2">
        <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}>
          Prev
        </button>
        <button
          onClick={() =>
            setPage(page + 1)
          }
          disabled={data ? (page + 1) * limit >= data.total : false}
        >
          Next
        </button>
      </div>
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => ({
  props: {},
  revalidate: 60,
});
export default withPageAuthRequired(AuditLogsPage);
