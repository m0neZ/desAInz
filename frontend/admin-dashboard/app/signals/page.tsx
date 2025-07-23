'use client';
import { useEffect, useState } from 'react';
import { trpc, type Signal } from '../../src/trpc';

const LIMIT = 20;

export default function SignalsPage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const load = async (p: number) => {
    const items = await trpc.signals.list(p, LIMIT);
    setSignals((prev) => (p === 1 ? items : [...prev, ...items]));
    if (items.length < LIMIT) {
      setHasMore(false);
    }
  };

  useEffect(() => {
    void load(1);
  }, []);

  const loadMore = () => {
    const next = page + 1;
    setPage(next);
    void load(next);
  };

  return (
    <div className="space-y-2">
      <h1>Signals</h1>
      <ul>
        {signals.map((s) => (
          <li key={s.id}>
            {s.source}: {s.content}
          </li>
        ))}
      </ul>
      {hasMore && (
        <button type="button" onClick={loadMore} className="border px-3 py-1">
          Load More
        </button>
      )}
    </div>
  );
}
