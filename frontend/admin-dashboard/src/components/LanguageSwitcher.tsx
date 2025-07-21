// @flow
import React from 'react';
import { useTranslation } from 'react-i18next';
import { useRouter } from 'next/router';
import { changeLanguage, supportedLngs } from '../i18n';

export function LanguageSwitcher() {
  const { t } = useTranslation();
  const router = useRouter();
  return (
    <div className="space-x-2" data-testid="language-switcher">
      {supportedLngs.map((lng) => (
        <button
          key={lng}
          type="button"
          aria-label={`Switch to ${lng === 'en' ? 'English' : 'Spanish'}`}
          onClick={() => {
            void changeLanguage(lng);
            void router.push(router.asPath, undefined, { locale: lng });
          }}
          data-testid={`lang-${lng}`}
        >
          {t(lng === 'en' ? 'english' : 'spanish')}
        </button>
      ))}
    </div>
  );
}
