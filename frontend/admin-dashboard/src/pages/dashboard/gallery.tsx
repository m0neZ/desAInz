import React, { useEffect, useState } from 'react';
import Image from 'next/image';
import type { GetStaticProps } from 'next';
import { useTranslation } from 'react-i18next';
import { trpc, type GalleryItem } from '../../trpc';

export default function GalleryPage() {
  const { t } = useTranslation();
  const [items, setItems] = useState<GalleryItem[]>([]);

  useEffect(() => {
    async function load() {
      setItems(await trpc.gallery.list());
    }
    void load();
  }, []);

  return (
    <div>
      <h1>{t('gallery')}</h1>
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
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => {
  return {
    props: {},
    revalidate: 60,
  };
};
