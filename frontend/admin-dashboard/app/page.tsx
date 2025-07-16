import { useTranslation } from 'react-i18next';

export default function Home() {
  const { t } = useTranslation();
  return (
    <main>
      <h1>{t('title')}</h1>
    </main>
  );
}
