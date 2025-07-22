// @flow
import React from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { useSignals } from '../../lib/trpc/hooks';

function SignalsPage() {
  const { t } = useTranslation();
  const { data: signals, isLoading } = useSignals();

  return (
    <div className="space-y-2">
      <h1>{t('signals')}</h1>
      {isLoading || !signals ? (
        <div>{t('loading')}</div>
      ) : (
        <ul>
          {signals.map((s) => (
            <li key={s.id}>
              {s.source}: {s.content}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => ({
  props: {},
  revalidate: 60,
});
export default withPageAuthRequired(SignalsPage);
