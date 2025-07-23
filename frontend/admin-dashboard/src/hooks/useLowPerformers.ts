import { useQuery } from '@tanstack/react-query';

export interface Performer {
  listing_id: number;
  revenue: number;
}

const base = process.env.NEXT_PUBLIC_ANALYTICS_URL ?? 'http://localhost:8000';

export function useLowPerformers(page: number, limit: number) {
  return useQuery({
    queryKey: ['lowPerformers', page, limit],
    queryFn: async () => {
      const res = await fetch(
        `${base}/low_performers?limit=${limit}&page=${page}`
      );
      if (!res.ok) {
        throw new Error('failed to load low performers');
      }
      return (await res.json()) as Performer[];
    },
  });
}
