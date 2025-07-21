import React, { useEffect, useState } from 'react';
import { fetchWithAuth } from '../hooks/useAuthFetch';

interface Assignment {
  username: string;
  role: string;
}

export function RolesList() {
  const [roles, setRoles] = useState<Assignment[]>([]);
  useEffect(() => {
    async function load() {
      const resp = await fetchWithAuth('/roles');
      if (resp.ok) {
        setRoles(await resp.json());
      }
    }
    void load();
  }, []);
  return (
    <ul aria-label="User roles">
      {roles.map((r) => (
        <li key={r.username}>
          {r.username}: {r.role}
        </li>
      ))}
    </ul>
  );
}
