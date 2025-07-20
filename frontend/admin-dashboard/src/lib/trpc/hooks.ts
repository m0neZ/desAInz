import { useQuery } from '@tanstack/react-query';
import { trpc } from '../../trpc';

export function useTrendingKeywords(limit: number = 10) {
  return useQuery({
    queryKey: ['trending', limit],
    queryFn: () => trpc.trending.list(limit),
  });
}

export function useAbTestSummary(abTestId: number) {
  return useQuery({
    queryKey: ['abTestSummary', abTestId],
    queryFn: () => trpc.abTests.summary(abTestId),
  });
}
