import React, { useEffect, useState } from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import { useTranslation } from 'react-i18next';

function PreferencesPage() {
  const { t } = useTranslation();
  const [notify, setNotify] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem('notifyFail');
    if (stored) {
      setNotify(stored === 'true');
    }
  }, []);

  const toggle = () => {
    const next = !notify;
    setNotify(next);
    localStorage.setItem('notifyFail', String(next));
  };

  return (
    <div className="space-y-2">
      <label className="flex items-center space-x-2">
        <input type="checkbox" checked={notify} onChange={toggle} />
        <span>{t('notifyOnFail')}</span>
      </label>
    </div>
  );
}
export default withPageAuthRequired(PreferencesPage);
