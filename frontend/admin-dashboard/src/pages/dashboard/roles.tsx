import React, { useState } from 'react';

export default function RolesPage() {
  const [userId, setUserId] = useState('');
  const [role, setRole] = useState('viewer');

  async function assign(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    await fetch('/roles/assign', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, role }),
    });
    setUserId('');
  }

  return (
    <form onSubmit={assign} className="space-y-2">
      <input
        className="border p-2"
        placeholder="User ID"
        value={userId}
        onChange={(e) => setUserId(e.target.value)}
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
      <button className="bg-blue-500 text-white px-4 py-2" type="submit">
        Assign Role
      </button>
    </form>
  );
}
