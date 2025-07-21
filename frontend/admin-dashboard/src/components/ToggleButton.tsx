// @flow
import React, { useState } from 'react';

/**
 * Button that toggles between "On" and "Off" when clicked.
 */
export function ToggleButton() {
  const [on, setOn] = useState(false);

  const toggle = () => setOn(!on);

  const onKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      toggle();
    }
  };

  return (
    <button
      aria-label="Toggle"
      aria-pressed={on}
      onClick={toggle}
      onKeyDown={onKeyDown}
      data-testid="toggle-button"
    >
      {on ? 'On' : 'Off'}
    </button>
  );
}
