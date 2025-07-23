// @flow
import React, { useEffect, useState } from 'react';

export default function LatencyIndicator() {
  const [hours, setHours] = useState<number | null>(null);
  const base =
    process.env.NEXT_PUBLIC_MONITORING_URL ?? 'http://localhost:8000';
  useEffect(() => {
    async function fetchLatency() {
      try {
        const res = await fetch(`${base}/latency`);
        if (res.ok) {
          const data = await res.json();
          setHours(data.average_seconds / 3600);
        }
      } catch {
        /* ignore */
      }
    }

    let id: NodeJS.Timeout | null = null;

    function start() {
      void fetchLatency();
      id = setInterval(fetchLatency, 5000);
    }

    function stop() {
      if (id) {
        clearInterval(id);
        id = null;
      }
    }

    function handleVisibility() {
      if (document.visibilityState === 'visible') {
        start();
      } else {
        stop();
      }
    }

    handleVisibility();
    document.addEventListener('visibilitychange', handleVisibility);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibility);
      stop();
    };
  }, [base]);

  if (hours === null) {
    return <div>Loading...</div>;
  }
  return (
    <div data-testid="latency-indicator">
      {`Avg time from signal to publish: ${hours.toFixed(2)}h`}
    </div>
  );
}
