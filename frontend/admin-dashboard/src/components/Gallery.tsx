// @flow
import React, { useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useGalleryItems } from '../lib/trpc/hooks';
import PaginationControls from './PaginationControls';

type Props = {
  limit?: number;
};

/**
 * Display a grid of gallery items with pagination using ``useGalleryItems``.
 */
export function Gallery({ limit = 20 }: Props) {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useGalleryItems(page, limit);

  if (isLoading || !data) {
    return <div data-testid="gallery-loading">Loading...</div>;
  }
  return (
    <>
      <div className="grid grid-cols-3 gap-2" data-testid="gallery">
        {data.items.map((item) => (
          <Link key={item.id} href={`/dashboard/publish?mockupId=${item.id}`}>
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
        limit={limit}
        onPageChange={setPage}
      />
    </>
  );
}
