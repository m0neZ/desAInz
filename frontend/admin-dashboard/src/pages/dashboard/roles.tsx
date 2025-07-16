import React from 'react';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import dynamic from 'next/dynamic';

const RolesList = dynamic(() => import('../../components/RolesList'));

export default function RolesPage() {
  const { t } = useTranslation();
  return (
    <div>
      <h1>{t('roles')}</h1>
      <RolesList />
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => {
  return {
    props: {},
    revalidate: 60,
  };
};
