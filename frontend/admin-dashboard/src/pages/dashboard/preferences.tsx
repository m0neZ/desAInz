import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

export default function PreferencesPage() {
  const { t } = useTranslation();
  const [emailAlerts, setEmailAlerts] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem('emailAlerts');
    if (stored) {
      setEmailAlerts(stored === 'true');
    }
  }, []);

  const toggle = () => {
    const value = !emailAlerts;
    setEmailAlerts(value);
    localStorage.setItem('emailAlerts', String(value));
  };

  return (
    <div className="space-y-2">
      <label className="flex items-center space-x-2">
        <input type="checkbox" checked={emailAlerts} onChange={toggle} />
        <span>{t('emailAlerts')}</span>
      </label>
    </div>
  );
}
