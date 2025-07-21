'use client';
import { useEffect, useState } from 'react';
import { trpc, type PublishTask } from '../../src/trpc';

export default function PublishPage() {
  const [tasks, setTasks] = useState<PublishTask[]>([]);

  useEffect(() => {
    async function load() {
      setTasks(await trpc.publishTasks.list());
    }
    void load();
  }, []);

  return (
    <div className="space-y-2">
      <h1>Publish Tasks</h1>
      <ul>
        {tasks.map((task) => (
          <li key={task.id}>
            {task.title} - {task.status}
          </li>
        ))}
      </ul>
    </div>
  );
}
