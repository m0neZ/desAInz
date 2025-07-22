// @flow
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

export function useSignals(page: number = 1, limit: number = 20) {
  return useQuery({
    queryKey: ['signals', page, limit],
    queryFn: () => trpc.signals.list(page, limit),
  });
}

export function useGalleryItems(page: number = 1, limit: number = 20) {
  return useQuery({
    queryKey: ['gallery', page, limit],
    queryFn: () => trpc.gallery.list(page, limit),
  });
}

export function useHeatmap() {
  return useQuery({
    queryKey: ['heatmap'],
    queryFn: () => trpc.heatmap.list(),
  });
}

export function usePublishTasks(page: number = 1, limit: number = 20) {
  return useQuery({
    queryKey: ['publishTasks', page, limit],
    queryFn: () => trpc.publishTasks.list(page, limit),
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

export function useAuditLogs(page: number = 1, limit: number = 50) {
  return useQuery({
    queryKey: ['auditLogs', page, limit],
    queryFn: () => trpc.auditLogs.list(page, limit),
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

export function useMockups(page: number = 1, limit: number = 20) {
  return useQuery({
    queryKey: ['mockups', page, limit],
    queryFn: () => trpc.mockups.list(page, limit),
  });
}

export function usePendingRuns() {
  return useQuery({
    queryKey: ['pendingRuns'],
    queryFn: () => trpc.approvals.list(),
  });
}
