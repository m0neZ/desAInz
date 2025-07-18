import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

export const supportedLngs = ['en', 'es'] as const;
export type SupportedLng = (typeof supportedLngs)[number];

const loaders: Record<SupportedLng, () => Promise<Record<string, string>>> = {
  en: async () => (await import('./locales/en/common.json')).default,
  es: async () => (await import('./locales/es/common.json')).default,
};

async function loadResources(lng: SupportedLng) {
  const resources = await loaders[lng]();
  if (!i18n.hasResourceBundle(lng, 'translation')) {
    i18n.addResourceBundle(lng, 'translation', resources);
  }
}

void i18n.use(initReactI18next).init({
  resources: {},
  lng: 'en',
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false,
  },
});

void loadResources('en');

export async function changeLanguage(lng: SupportedLng) {
  await loadResources(lng);
  await i18n.changeLanguage(lng);
}

export default i18n;
