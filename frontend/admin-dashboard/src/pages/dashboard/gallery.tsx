import React from 'react';

export async function getStaticProps() {
  return { props: {}, revalidate: 60 };
}

export default function GalleryPage() {
  return <div>Gallery page placeholder.</div>;
}
