// @flow
import React from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import { useTranslation } from 'react-i18next';
import { usePreferenceStore } from '../../store/usePreferenceStore';

function PreferencesPage() {
  const { t } = useTranslation();
  const notify = usePreferenceStore((s) => s.notifyFail);
  const setNotify = usePreferenceStore((s) => s.setNotifyFail);

  const toggle = () => {
    setNotify(!notify);
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
