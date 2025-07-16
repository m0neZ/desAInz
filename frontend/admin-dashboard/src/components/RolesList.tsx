import React, { useEffect, useState } from 'react';

interface Assignment {
  username: string;
  role: string;
}

export function RolesList() {
  const [roles, setRoles] = useState<Assignment[]>([]);
  useEffect(() => {
    async function load() {
      const resp = await fetch('/roles', {
        headers: { Authorization: 'Bearer ' + localStorage.getItem('token') },
      });
      if (resp.ok) {
        setRoles(await resp.json());
      }
    }
    void load();
  }, []);
  return (
    <ul>
      {roles.map((r) => (
        <li key={r.username}>
          {r.username}: {r.role}
        </li>
      ))}
    </ul>
  );
}
