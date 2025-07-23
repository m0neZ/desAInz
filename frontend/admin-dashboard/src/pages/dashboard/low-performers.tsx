// @flow
import React, { useState } from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import { useTranslation } from 'react-i18next';
import PaginationControls from '../../components/PaginationControls';
import { useLowPerformers } from '../../hooks/useLowPerformers';

import type { Performer } from '../../hooks/useLowPerformers';

const LIMIT = 20;

function LowPerformersPage() {
  const { t } = useTranslation();
  const [page, setPage] = useState(1);
  const { data: items, isLoading } = useLowPerformers(page, LIMIT);

  return (
    <div className="space-y-2">
      <h2 className="text-lg font-bold">{t('lowPerformers')}</h2>
      {isLoading || !items ? (
        <div>{t('loading')}</div>
      ) : (
        <ul>
          {items.map((p) => (
            <li key={p.listing_id} className="text-red-600">
              {p.listing_id}: ${p.revenue.toFixed(2)}
            </li>
          ))}
        </ul>
      )}
      <PaginationControls
        page={page}
        total={null}
        limit={LIMIT}
        onPageChange={setPage}
      />
    </div>
  );
}
export default withPageAuthRequired(LowPerformersPage);
