import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    res.status(405).end();
    return;
  }
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/maintenance/run`,
    {
      method: 'POST',
      headers: {
        Authorization: req.headers.authorization ?? '',
      },
    }
  );
  const body = await response.json();
  res.status(response.status).json(body);
}
