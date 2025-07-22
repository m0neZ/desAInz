// @flow
import React from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import dynamic from 'next/dynamic';
import { useState } from 'react';

const RolesList = dynamic(() => import('../../components/RolesList'));

function RolesPage() {
  const { t } = useTranslation();
  const [page, setPage] = useState(0);
  const limit = 50;
  return (
    <div>
      <h1>{t('roles')}</h1>
      <RolesList limit={limit} page={page} />
      <div className="space-x-2">
        <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}>
          Prev
        </button>
        <button onClick={() => setPage(page + 1)}>Next</button>
      </div>
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => {
  return {
    props: {},
    revalidate: 60,
  };
};
export default withPageAuthRequired(RolesPage);
