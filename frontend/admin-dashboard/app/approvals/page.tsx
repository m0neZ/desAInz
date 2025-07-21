'use client';
import { useState } from 'react';
import { Button } from '../../src/components/Button';
import { trpc } from '../../src/trpc';

export default function ApprovalsPage() {
  const [runId, setRunId] = useState('');
  const [status, setStatus] = useState('');

  async function approve() {
    try {
      await trpc.approvals.approve(runId);
      setStatus('Approved');
    } catch {
      setStatus('Approval failed');
    }
  }

  return (
    <div className="space-y-2">
      <h1>Approvals</h1>
      <input
        className="border p-2"
        value={runId}
        onChange={(e) => setRunId(e.target.value)}
        placeholder="Run ID"
      />
      <Button onClick={approve}>Approve</Button>
      {status && <p>{status}</p>}
    </div>
  );
}
