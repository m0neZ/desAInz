// @flow
/**
 * React hook providing live metrics via WebSocket.
 *
 * The connection automatically retries with exponential backoff when it closes
 * unexpectedly. The number of retry attempts is determined by the
 * `NEXT_PUBLIC_WS_MAX_RETRIES` environment variable which defaults to `5`.
 */
import { useEffect, useRef, useState } from 'react';

export interface LiveMetrics {
  cpu_percent?: number;
  memory_mb?: number;
  active_users?: number;
  error_rate?: number;
}

export function useLiveMetrics() {
  const [metrics, setMetrics] = useState<LiveMetrics | null>(null);
  const retries = useRef(0);
  const maxRetries = parseInt(
    process.env.NEXT_PUBLIC_WS_MAX_RETRIES ?? '5',
    10
  );

  const wsRef = useRef<WebSocket | null>(null);
  const closedByUser = useRef(false);

  useEffect(() => {
    closedByUser.current = false;

    function connect() {
      if (retries.current > maxRetries) {
        return;
      }
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      const ws = new WebSocket(
        `${protocol}://${window.location.host}/ws/metrics`
      );
      wsRef.current = ws;
      ws.onmessage = (event) => {
        try {
          setMetrics(JSON.parse(event.data) as LiveMetrics);
        } catch {
          // ignore invalid messages
        }
      };
      ws.onclose = () => {
        if (!closedByUser.current && retries.current < maxRetries) {
          retries.current += 1;
          const delay = Math.min(2 ** retries.current * 1000, 30000);
          setTimeout(connect, delay);
        }
      };
    }

    connect();

    return () => {
      closedByUser.current = true;
      wsRef.current?.close();
    };
  }, [maxRetries]);

  return metrics;
}
