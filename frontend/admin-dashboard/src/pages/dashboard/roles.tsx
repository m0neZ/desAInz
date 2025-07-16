import React, { useEffect, useState } from 'react';
import type { GetStaticProps } from 'next';
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

export const getStaticProps: GetStaticProps = async () => {
  return {
    props: {},
    revalidate: 60,
  };
};
