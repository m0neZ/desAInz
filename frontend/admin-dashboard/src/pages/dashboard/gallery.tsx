import dynamic from 'next/dynamic';
import React from 'react';

const Gallery = dynamic(() => import('../../features/Gallery'));

export default function GalleryPage() {
  return <Gallery />;
}
