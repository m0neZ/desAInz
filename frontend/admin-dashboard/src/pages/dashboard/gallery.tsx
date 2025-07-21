import React from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import Image from 'next/image';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { useGalleryItems } from '../../lib/trpc/hooks';

function GalleryPage() {
  const { t } = useTranslation();
  const { data: items, isLoading } = useGalleryItems();

  return (
    <div>
      <h1>{t('gallery')}</h1>
      {isLoading || !items ? (
        <div>{t('loading')}</div>
      ) : (
        <div className="grid grid-cols-3 gap-2">
          {items.map((item) => (
            <Image
              key={item.id}
              src={item.imageUrl}
              alt={item.title}
              width={200}
              height={200}
              className="border"
            />
          ))}
        </div>
      )}
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => {
  return {
    props: {},
    revalidate: 60,
  };
};
export default withPageAuthRequired(GalleryPage);
