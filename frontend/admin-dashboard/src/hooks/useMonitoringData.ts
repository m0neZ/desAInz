import { useEffect, useState } from 'react';

export interface MetricPoint {
  timestamp: string;
  value: number;
}

export function useAnalyticsData(range: string) {
  const [data, setData] = useState<MetricPoint[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const resp = await fetch(`/api/monitoring/analytics?range=${range}`);
        if (resp.ok) {
          const body = await resp.json();
          setData(body.metrics ?? []);
        }
      } catch {
        setData([]);
      }
    }
    void load();
  }, [range]);

  return data;
}

export function useLatencyData(range: string) {
  const [data, setData] = useState<MetricPoint[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const resp = await fetch(`/api/monitoring/latency?range=${range}`);
        if (resp.ok) {
          const body = await resp.json();
          setData(body.metrics ?? []);
        }
      } catch {
        setData([]);
      }
    }
    void load();
  }, [range]);

  return data;
}

export function useAlertStatus(thresholdHours: number) {
  const [alert, setAlert] = useState(false);

  useEffect(() => {
    async function check() {
      try {
        const resp = await fetch('/api/monitoring/latency');
        if (resp.ok) {
          const body = await resp.json();
          if (body.average_seconds > thresholdHours * 3600) {
            setAlert(true);
          } else {
            setAlert(false);
          }
        }
      } catch {
        setAlert(false);
      }
    }
    void check();
    const id = setInterval(check, 60000);
    return () => clearInterval(id);
  }, [thresholdHours]);

  return alert;
}
