// @flow
import React from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import Image from 'next/image';
import Link from 'next/link';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { useMockups } from '../../lib/trpc/hooks';

function MockupGalleryPage() {
  const { t } = useTranslation();
  const { data: mockups, isLoading } = useMockups();

  return (
    <div>
      <h1>{t('mockupGallery')}</h1>
      {isLoading || !mockups ? (
        <div>{t('loading')}</div>
      ) : (
        <div className="grid grid-cols-3 gap-2">
          {mockups.map((m) => (
            <Link key={m.id} href={`/dashboard/publish?mockupId=${m.id}`}>
              <Image
                src={m.imageUrl}
                alt={m.id.toString()}
                width={200}
                height={200}
                className="border"
              />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => ({
  props: {},
  revalidate: 60,
});
export default withPageAuthRequired(MockupGalleryPage);
