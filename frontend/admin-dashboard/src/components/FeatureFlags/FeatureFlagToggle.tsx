// @flow
import React from 'react';

interface Props {
  name: string;
  enabled: boolean;
  onToggle: (value: boolean) => void;
}

export function FeatureFlagToggle({ name, enabled, onToggle }: Props) {
  return (
    <label>
      <input
        type="checkbox"
        checked={enabled}
        onChange={(e) => onToggle(e.target.checked)}
      />
      {name}
    </label>
  );
}
