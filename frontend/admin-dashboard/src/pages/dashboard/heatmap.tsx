import React from 'react';

export async function getStaticProps() {
  return { props: {}, revalidate: 60 };
}

export default function HeatmapPage() {
  return <div>Heatmap page placeholder.</div>;
}
