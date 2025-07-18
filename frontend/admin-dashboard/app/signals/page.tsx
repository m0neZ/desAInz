import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { trpc, type Signal } from '../../src/trpc';

export default function SignalsPage() {
  const { t } = useTranslation();
  const [signals, setSignals] = useState<Signal[]>([]);

  useEffect(() => {
    async function load() {
      setSignals(await trpc.signals.list());
    }
    void load();
  }, []);

  return (
    <div className="space-y-2">
      <h1>{t('signals')}</h1>
      <ul>
        {signals.map((s) => (
          <li key={s.id}>
            {s.source}: {s.content}
          </li>
        ))}
      </ul>
    </div>
  );
}
