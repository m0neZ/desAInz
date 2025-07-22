// @flow
import React from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import Image from 'next/image';
import Link from 'next/link';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { useMockups } from '../../lib/trpc/hooks';
import { useState } from 'react';

function MockupGalleryPage() {
  const { t } = useTranslation();
  const [page, setPage] = useState(0);
  const limit = 100;
  const { data: mockups, isLoading } = useMockups(limit, page);

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
      <div className="space-x-2">
        <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}>
          Prev
        </button>
        <button onClick={() => setPage(page + 1)}>Next</button>
      </div>
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => ({
  props: {},
  revalidate: 60,
});
export default withPageAuthRequired(MockupGalleryPage);
