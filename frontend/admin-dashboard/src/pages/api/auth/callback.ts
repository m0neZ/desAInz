import type { NextApiRequest, NextApiResponse } from 'next';
import { auth0 } from '../../../lib/auth0';

export default async function callback(req: NextApiRequest, res: NextApiResponse) {
  await auth0.handleCallback(req, res);
}
