// @flow
import { Auth0Client } from '@auth0/nextjs-auth0/server';

export const auth0 = new Auth0Client({
  domain: process.env.AUTH0_DOMAIN ?? '',
  clientId: process.env.AUTH0_CLIENT_ID ?? '',
  clientSecret: process.env.AUTH0_CLIENT_SECRET ?? '',
  secret: process.env.AUTH0_SECRET ?? 'insecure',
  baseURL: process.env.APP_BASE_URL ?? 'http://localhost:3000',
});
