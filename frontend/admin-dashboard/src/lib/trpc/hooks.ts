// @flow
import { useQuery } from '@tanstack/react-query';
import { trpc } from '../../trpc';

export function useTrendingKeywords(limit: number = 10, page: number = 0) {
  return useQuery({
    queryKey: ['trending', limit, page],
    queryFn: () => trpc.trending.list(limit, page),
  });
}

export function useAbTestSummary(abTestId: number) {
  return useQuery({
    queryKey: ['abTestSummary', abTestId],
    queryFn: () => trpc.abTests.summary(abTestId),
  });
}

export function useSignals() {
  return useQuery({
    queryKey: ['signals'],
    queryFn: () => trpc.signals.list(),
  });
}

export function useGalleryItems() {
  return useQuery({
    queryKey: ['gallery'],
    queryFn: () => trpc.gallery.list(),
  });
}

export function useHeatmap() {
  return useQuery({
    queryKey: ['heatmap'],
    queryFn: () => trpc.heatmap.list(),
  });
}

export function usePublishTasks(limit = 50, page = 0) {
  return useQuery({
    queryKey: ['publishTasks', limit, page],
    queryFn: () => trpc.publishTasks.list(limit, page),
  });
}

export function useAnalyticsSummary() {
  return useQuery({
    queryKey: ['analyticsSummary'],
    queryFn: () => trpc.analytics.summary(),
  });
}

export function useMetrics() {
  return useQuery({
    queryKey: ['metrics'],
    queryFn: () => trpc.metrics.list(),
  });
}

export function useMetricsSummary() {
  return useQuery({
    queryKey: ['metricsSummary'],
    queryFn: () => trpc.metrics.summary(),
  });
}

export function useAuditLogs(limit = 50, page = 0) {
  return useQuery({
    queryKey: ['auditLogs', limit, page],
    queryFn: () => trpc.auditLogs.list(limit, page),
  });
}

export function useOptimizations() {
  return useQuery({
    queryKey: ['optimizations'],
    queryFn: () => trpc.optimizations.list(),
  });
}

export function useOptimizationRecommendations() {
  return useQuery({
    queryKey: ['optimizationRecommendations'],
    queryFn: () => trpc.recommendations.list(),
  });
}

export function useMockups(limit = 100, page = 0) {
  return useQuery({
    queryKey: ['mockups', limit, page],
    queryFn: () => trpc.mockups.list(limit, page),
  });
}

export function usePendingRuns() {
  return useQuery({
    queryKey: ['pendingRuns'],
    queryFn: () => trpc.approvals.list(),
  });
}
