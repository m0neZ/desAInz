// @flow
import React, { useState } from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import Image from 'next/image';
import Link from 'next/link';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { useGalleryItems } from '../../lib/trpc/hooks';
import PaginationControls from '../../components/PaginationControls';

const LIMIT = 20;

function GalleryPage() {
  const { t } = useTranslation();
  const [page, setPage] = useState(1);
  const { data, isLoading } = useGalleryItems(page, LIMIT);

  return (
    <div>
      <h1>{t('gallery')}</h1>
      {isLoading || !data ? (
        <div>{t('loading')}</div>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-2">
            {data.items.map((item) => (
              <Link
                key={item.id}
                href={`/dashboard/publish?mockupId=${item.id}`}
              >
                <Image
                  src={item.imageUrl}
                  alt={item.title}
                  width={200}
                  height={200}
                  className="border"
                />
              </Link>
            ))}
          </div>
          <PaginationControls
            page={page}
            total={data.total}
            limit={LIMIT}
            onPageChange={setPage}
          />
        </>
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
