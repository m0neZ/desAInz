import dynamic from 'next/dynamic';
import React from 'react';

const AbTests = dynamic(() => import('../../features/AbTests'));

export default function AbTestsPage() {
  return <AbTests />;
}
