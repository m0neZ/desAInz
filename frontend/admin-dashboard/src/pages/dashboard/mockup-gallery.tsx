// @flow
import React, { useState } from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import Image from 'next/image';
import Link from 'next/link';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { useMockups } from '../../lib/trpc/hooks';
import PaginationControls from '../../components/PaginationControls';

const LIMIT = 20;

function MockupGalleryPage() {
  const { t } = useTranslation();
  const [page, setPage] = useState(1);
  const { data, isLoading } = useMockups(page, LIMIT);

  return (
    <div>
      <h1>{t('mockupGallery')}</h1>
      {isLoading || !data ? (
        <div>{t('loading')}</div>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-2">
            {data.items.map((m) => (
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

export const getStaticProps: GetStaticProps = async () => ({
  props: {},
  revalidate: 60,
});
export default withPageAuthRequired(MockupGalleryPage);
