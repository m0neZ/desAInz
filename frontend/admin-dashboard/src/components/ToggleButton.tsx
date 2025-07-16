import React, { useState } from 'react';

/**
 * Button that toggles between "On" and "Off" when clicked.
 */
export function ToggleButton() {
  const [on, setOn] = useState(false);
  return (
    <button onClick={() => setOn(!on)} data-testid="toggle-button">
      {on ? 'On' : 'Off'}
    </button>
  );
}
