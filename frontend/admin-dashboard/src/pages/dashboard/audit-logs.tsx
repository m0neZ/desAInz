// @flow
import React, { useState } from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { useAuditLogs } from '../../lib/trpc/hooks';
import PaginationControls from '../../components/PaginationControls';

const LIMIT = 20;

function AuditLogsPage() {
  const { t } = useTranslation();
  const [page, setPage] = useState(1);
  const { data, isLoading } = useAuditLogs(page, LIMIT);

  return (
    <div className="space-y-2">
      <h1>{t('auditLogs')}</h1>
      {isLoading || !data ? (
        <div>{t('loading')}</div>
      ) : (
        <>
          <ul>
            {data.items.map((log) => (
              <li
                key={log.id}
              >{`${log.timestamp} ${log.username} ${log.action}`}</li>
            ))}
          </ul>
          <PaginationControls
            page={page}
            total={data.total}
            limit={LIMIT}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => ({
  props: {},
  revalidate: 60,
});
export default withPageAuthRequired(AuditLogsPage);
