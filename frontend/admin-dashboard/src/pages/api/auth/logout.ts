// @flow
import type { NextApiRequest, NextApiResponse } from 'next';
import { auth0 } from '../../../lib/auth0';

export default async function logout(
  req: NextApiRequest,
  res: NextApiResponse
) {
  await auth0.handleLogout(req, res);
}
