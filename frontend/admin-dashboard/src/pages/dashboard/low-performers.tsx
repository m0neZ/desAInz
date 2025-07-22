// @flow
import React, { useEffect, useState } from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import { useTranslation } from 'react-i18next';
import PaginationControls from '../../components/PaginationControls';

interface Performer {
  listing_id: number;
  revenue: number;
}

const LIMIT = 20;

function LowPerformersPage() {
  const { t } = useTranslation();
  const [items, setItems] = useState<Performer[]>([]);
  const [page, setPage] = useState(1);
  const base = process.env.NEXT_PUBLIC_ANALYTICS_URL ?? 'http://localhost:8000';
  useEffect(() => {
    async function fetchData() {
      try {
        const res = await fetch(
          `${base}/low_performers?limit=${LIMIT}&page=${page}`
        );
        if (res.ok) {
          setItems(await res.json());
        }
      } catch {
        /* ignore */
      }
    }
    void fetchData();
  }, [base, page]);

  return (
    <div className="space-y-2">
      <h2 className="text-lg font-bold">{t('lowPerformers')}</h2>
      <ul>
        {items.map((p) => (
          <li key={p.listing_id} className="text-red-600">
            {p.listing_id}: ${p.revenue.toFixed(2)}
          </li>
        ))}
      </ul>
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
