import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '../../components/Button';
import { trpc } from '../../trpc';

export default function RolesPage() {
  const { t } = useTranslation();
  const [userId, setUserId] = useState('');
  const [role, setRole] = useState('viewer');

  async function assign() {
    await trpc.assignRole.mutate({ userId, role });
    setUserId('');
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">{t('roles')}</h1>
      <input
        className="border p-2"
        value={userId}
        onChange={(e) => setUserId(e.target.value)}
        placeholder="User ID"
      />
      <select
        className="border p-2"
        value={role}
        onChange={(e) => setRole(e.target.value)}
      >
        <option value="admin">admin</option>
        <option value="editor">editor</option>
        <option value="viewer">viewer</option>
      </select>
      <Button onClick={assign}>{t('roles')}</Button>
    </div>
  );
}
