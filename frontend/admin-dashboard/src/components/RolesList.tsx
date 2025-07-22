// @flow
import React, { useEffect, useState } from 'react';
import { fetchWithAuth } from '../hooks/useAuthFetch';
import PaginationControls from './PaginationControls';

/**
 * Paginated list of user role assignments.
 */

interface Assignment {
  username: string;
  role: string;
}

const LIMIT = 20;

export function RolesList() {
  const [roles, setRoles] = useState<Assignment[]>([]);
  const [page, setPage] = useState(1);

  useEffect(() => {
    async function load() {
      const resp = await fetchWithAuth(`/roles?page=${page}&limit=${LIMIT}`);
      if (resp.ok) {
        setRoles(await resp.json());
      }
    }
    void load();
  }, [page]);
  return (
    <>
      <ul aria-label="User roles">
        {roles.map((r) => (
          <li key={r.username}>
            {r.username}: {r.role}
          </li>
        ))}
      </ul>
      <PaginationControls
        page={page}
        total={null}
        limit={LIMIT}
        onPageChange={setPage}
      />
    </>
  );
}
