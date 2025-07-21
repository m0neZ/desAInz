// @flow
import React from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';

function ZazzlePage() {
  return <div>Zazzle integration coming soon.</div>;
}

export const getStaticProps = async () => ({ props: {}, revalidate: 60 });
export default withPageAuthRequired(ZazzlePage);
