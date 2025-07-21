// @flow
/**
 * React hook providing live metrics via WebSocket.
 */
import { useEffect, useState } from 'react';

export interface LiveMetrics {
  cpu_percent?: number;
  memory_mb?: number;
  active_users?: number;
  error_rate?: number;
}

export function useLiveMetrics() {
  const [metrics, setMetrics] = useState<LiveMetrics | null>(null);

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(
      `${protocol}://${window.location.host}/ws/metrics`
    );
    ws.onmessage = (event) => {
      try {
        setMetrics(JSON.parse(event.data) as LiveMetrics);
      } catch {
        // ignore invalid messages
      }
    };
    return () => {
      ws.close();
    };
  }, []);

  return metrics;
}
