// @flow
import React, { useEffect, useState } from 'react';

interface StatusMap {
  [key: string]: string;
}

export default function StatusIndicator() {
  const [status, setStatus] = useState<StatusMap>({});
  const url = process.env.NEXT_PUBLIC_API_HEALTH_URL ?? '/api/health';

  useEffect(() => {
    async function fetchStatus() {
      try {
        const res = await fetch(url);
        if (res.ok) {
          setStatus(await res.json());
        }
      } catch {
        /* ignore */
      }
    }
    fetchStatus();
    const id = setInterval(fetchStatus, 5000);
    return () => clearInterval(id);
  }, [url]);

  return (
    <div className="space-y-2">
      {Object.entries(status).map(([service, state]) => (
        <div key={service}>
          {service}:{' '}
          <span className={state === 'ok' ? 'text-green-600' : 'text-red-600'}>
            {state}
          </span>
        </div>
      ))}
    </div>
  );
}
