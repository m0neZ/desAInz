import dynamic from 'next/dynamic';
import React from 'react';

const Heatmap = dynamic(() => import('../../features/Heatmap'));

export default function HeatmapPage() {
  return <Heatmap />;
}
