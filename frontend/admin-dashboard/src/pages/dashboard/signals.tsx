// @flow
import React, { useState } from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { useSignals } from '../../lib/trpc/hooks';
import PaginationControls from '../../components/PaginationControls';

const LIMIT = 20;

function SignalsPage() {
  const { t } = useTranslation();
  const [page, setPage] = useState(1);
  const { data: signals, isLoading } = useSignals(page, LIMIT);

  return (
    <div className="space-y-2">
      <h1>{t('signals')}</h1>
      {isLoading || !signals ? (
        <div>{t('loading')}</div>
      ) : (
        <>
          <ul>
            {signals.items.map((s) => (
              <li key={s.id}>
                {s.source}: {s.content}
              </li>
            ))}
          </ul>
          <PaginationControls
            page={page}
            total={signals.total}
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
export default withPageAuthRequired(SignalsPage);
