// @flow
import React, { useEffect } from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import { useTranslation } from 'react-i18next';
import { usePreferencesStore } from '../../store/usePreferencesStore';

function PreferencesPage() {
  const { t } = useTranslation();
  const notify = usePreferencesStore((s) => s.notifyOnFail);
  const toggleNotify = usePreferencesStore((s) => s.toggleNotify);

  useEffect(() => {
    // hydrate persisted state on mount
    usePreferencesStore.persist.rehydrate();
  }, []);

  const toggle = () => {
    toggleNotify();
  };

  return (
    <div className="space-y-2">
      <label className="flex items-center space-x-2">
        <input
          type="checkbox"
          checked={notify}
          onChange={toggle}
          className="focus:ring"
          aria-label={t('notifyOnFail')}
        />
        <span>{t('notifyOnFail')}</span>
      </label>
    </div>
  );
}
export default withPageAuthRequired(PreferencesPage);
