import React, { useEffect, useState } from 'react';
import { Button } from '../../components/Button';

interface Task {
  id: number;
  status: string;
  metadata: Record<string, unknown> | null;
}

export default function PublishTasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [metadataEdits, setMetadataEdits] = useState<Record<number, string>>(
    {}
  );

  useEffect(() => {
    fetch('/api/tasks')
      .then((res) => res.json())
      .then(setTasks)
      .catch(() => setTasks([]));
  }, []);

  const retry = async (taskId: number) => {
    await fetch(`/api/tasks/${taskId}/retry`, { method: 'POST' });
  };

  const save = async (taskId: number) => {
    const payload = metadataEdits[taskId];
    if (!payload) return;
    await fetch(`/api/tasks/${taskId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ metadata: JSON.parse(payload) }),
    });
  };

  return (
    <div>
      <h1>Publish Tasks</h1>
      <ul>
        {tasks.map((t) => (
          <li key={t.id} className="mb-4">
            <div>
              #{t.id} - {t.status}
            </div>
            <textarea
              defaultValue={JSON.stringify(t.metadata)}
              onChange={(e) =>
                setMetadataEdits({
                  ...metadataEdits,
                  [t.id]: e.target.value,
                })
              }
              className="w-full border"
            />
            <Button onClick={() => save(t.id)} className="mr-2 mt-2">
              Save
            </Button>
            <Button onClick={() => retry(t.id)} className="mt-2">
              Retry
            </Button>
          </li>
        ))}
      </ul>
    </div>
  );
}
