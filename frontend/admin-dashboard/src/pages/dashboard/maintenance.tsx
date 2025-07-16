import React, { useState } from 'react';
import { Button } from '../../components/Button';

export default function MaintenancePage() {
  const [status, setStatus] = useState<string | null>(null);

  async function runMaintenance() {
    setStatus('running');
    const res = await fetch('/api/maintenance', { method: 'POST' });
    setStatus(res.ok ? 'done' : 'error');
  }

  return (
    <div>
      <h1>Maintenance</h1>
      <Button onClick={runMaintenance} data-testid="maintenance-button">
        Run Cleanup
      </Button>
      {status && <div data-testid="maintenance-status">{status}</div>}
    </div>
  );
}
