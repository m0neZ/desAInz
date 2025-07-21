'use client';
import { useEffect, useState } from 'react';
import { trpc, type Idea } from '../../src/trpc';

export default function IdeasPage() {
  const [ideas, setIdeas] = useState<Idea[]>([]);

  useEffect(() => {
    async function load() {
      setIdeas(await trpc.ideas.list());
    }
    void load();
  }, []);

  return (
    <div className="space-y-2">
      <h1>Ideas</h1>
      <ul>
        {ideas.map((idea) => (
          <li key={idea.id}>{idea.title}</li>
        ))}
      </ul>
    </div>
  );
}
