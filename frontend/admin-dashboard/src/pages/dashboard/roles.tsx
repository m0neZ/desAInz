import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

interface Assignment {
  username: string;
  role: string;
}

export default function RolesPage() {
  const { t } = useTranslation();
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
    <div>
      <h1>{t('roles')}</h1>
      <ul>
        {roles.map((r) => (
          <li key={r.username}>
            {r.username}: {r.role}
          </li>
        ))}
      </ul>
    </div>
  );
}
