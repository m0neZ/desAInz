import React, { useEffect, useState } from 'react';

export interface StatusData {
  cpu_percent: number;
  memory_mb: number;
}

export default function StatusIndicators() {
  const [data, setData] = useState<StatusData | null>(null);

  useEffect(() => {
    async function fetchStatus() {
      try {
        const res = await fetch('/api/status');
        if (res.ok) {
          setData(await res.json());
        }
      } catch {
        // ignore network errors for now
      }
    }
    fetchStatus();
    const id = setInterval(fetchStatus, 5000);
    return () => clearInterval(id);
  }, []);

  if (!data) {
    return <div>Loading status...</div>;
  }

  return (
    <div className="space-x-4">
      <span>CPU: {data.cpu_percent}%</span>
      <span>Memory: {data.memory_mb.toFixed(1)} MB</span>
    </div>
  );
}
