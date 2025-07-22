// @flow
import React, { useEffect, useState } from 'react';
import { fetchWithAuth } from '../../hooks/useAuthFetch';

/**
 * Manage and toggle all available feature flags.
 */

export function FeatureFlagsList() {
  const [flags, setFlags] = useState<Record<string, boolean>>({});
  useEffect(() => {
    async function load() {
      const res = await fetchWithAuth('/feature-flags');
      if (res.ok) {
        setFlags(await res.json());
      }
    }
    void load();
  }, []);

  async function toggle(name: string, value: boolean) {
    const res = await fetchWithAuth(
      `/feature-flags/${encodeURIComponent(name)}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: value }),
      }
    );
    if (res.ok) {
      setFlags((f) => ({ ...f, [name]: value }));
    }
  }

  return (
    <ul aria-label="Feature flags">
      {Object.entries(flags).map(([name, enabled]) => (
        <li key={name}>
          <label>
            <input
              type="checkbox"
              checked={enabled}
              onChange={(e) => toggle(name, e.target.checked)}
            />
            {name}
          </label>
        </li>
      ))}
    </ul>
  );
}
