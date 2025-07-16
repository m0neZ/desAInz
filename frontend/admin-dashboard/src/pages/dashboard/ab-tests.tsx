import React from 'react';

export async function getStaticProps() {
  return { props: {}, revalidate: 60 };
}

export default function AbTestsPage() {
  return <div>AB Tests page placeholder.</div>;
}
