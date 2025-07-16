import React, { useEffect, useState } from 'react';

interface Preferences {
  receiveNotifications: boolean;
}

export default function PreferencesPage() {
  const [prefs, setPrefs] = useState<Preferences>({
    receiveNotifications: true,
  });

  useEffect(() => {
    const raw = localStorage.getItem('prefs');
    if (raw) {
      setPrefs(JSON.parse(raw));
    }
  }, []);

  function toggleNotifications() {
    const next = {
      ...prefs,
      receiveNotifications: !prefs.receiveNotifications,
    };
    setPrefs(next);
    localStorage.setItem('prefs', JSON.stringify(next));
  }

  return (
    <div>
      <label className="flex items-center space-x-2">
        <input
          type="checkbox"
          checked={prefs.receiveNotifications}
          onChange={toggleNotifications}
        />
        <span>Enable Notifications</span>
      </label>
    </div>
  );
}
