'use client';
import { useEffect, useState } from 'react';
import Image from 'next/image';
import { trpc, type Mockup } from '../../src/trpc';

export default function MockupsPage() {
  const [mockups, setMockups] = useState<Mockup[]>([]);

  useEffect(() => {
    async function load() {
      setMockups(await trpc.mockups.list());
    }
    void load();
  }, []);

  return (
    <div>
      <h1>Mockups</h1>
      <div className="grid grid-cols-3 gap-2">
        {mockups.map((m) => (
          <Image
            key={m.id}
            src={m.imageUrl}
            alt={m.id.toString()}
            width={200}
            height={200}
          />
        ))}
      </div>
    </div>
  );
}
