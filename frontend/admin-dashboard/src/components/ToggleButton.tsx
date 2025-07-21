// @flow
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';

/**
 * Button that toggles between "On" and "Off" when clicked.
 */
export function ToggleButton() {
  const [on, setOn] = useState(false);
  const { t } = useTranslation();

  const toggle = () => setOn(!on);

  const onKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      toggle();
    }
  };

  return (
    <button
      aria-label={t('toggle')}
      aria-pressed={on}
      onClick={toggle}
      onKeyDown={onKeyDown}
      data-testid="toggle-button"
    >
      {on ? t('on') : t('off')}
    </button>
  );
}
