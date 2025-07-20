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

export function usePublishTasks() {
  return useQuery({
    queryKey: ['publishTasks'],
    queryFn: () => trpc.publishTasks.list(),
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

export function useAuditLogs(limit = 50, offset = 0) {
  return useQuery({
    queryKey: ['auditLogs', limit, offset],
    queryFn: () => trpc.auditLogs.list(limit, offset),
  });
}

export function useOptimizations() {
  return useQuery({
    queryKey: ['optimizations'],
    queryFn: () => trpc.optimizations.list(),
  });
}
