import React from 'react';
import { useTranslation } from 'react-i18next';
import { changeLanguage, supportedLngs } from '../i18n';

export function LanguageSwitcher() {
  const { t } = useTranslation();
  return (
    <div className="space-x-2" data-testid="language-switcher">
      {supportedLngs.map((lng) => (
        <button
          key={lng}
          type="button"
          onClick={() => changeLanguage(lng)}
          data-testid={`lang-${lng}`}
        >
          {t(lng === 'en' ? 'english' : 'spanish')}
        </button>
      ))}
    </div>
  );
}
