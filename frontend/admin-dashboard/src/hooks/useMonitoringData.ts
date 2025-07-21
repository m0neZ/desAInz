// @flow
import { useQuery } from '@tanstack/react-query';

export interface MetricPoint {
  timestamp: string;
  value: number;
}

export function useAnalyticsData(range: string) {
  return useQuery({
    queryKey: ['analyticsData', range],
    queryFn: async () => {
      const resp = await fetch(`/api/monitoring/analytics?range=${range}`);
      if (!resp.ok) {
        throw new Error('failed to load analytics');
      }
      const body = await resp.json();
      return (body.metrics ?? []) as MetricPoint[];
    },
  });
}

export function useLatencyData(range: string) {
  return useQuery({
    queryKey: ['latencyData', range],
    queryFn: async () => {
      const resp = await fetch(`/api/monitoring/latency?range=${range}`);
      if (!resp.ok) {
        throw new Error('failed to load latency');
      }
      const body = await resp.json();
      return (body.metrics ?? []) as MetricPoint[];
    },
  });
}

export function useAlertStatus(thresholdHours: number) {
  const { data } = useQuery({
    queryKey: ['alertStatus', thresholdHours],
    queryFn: async () => {
      const resp = await fetch('/api/monitoring/latency');
      if (!resp.ok) {
        return false;
      }
      const body = await resp.json();
      return body.average_seconds > thresholdHours * 3600;
    },
    refetchInterval: 60000,
  });

  return data ?? false;
}
