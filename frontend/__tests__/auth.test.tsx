import type { NextApiRequest, NextApiResponse } from 'next';
import login from '../admin-dashboard/src/pages/api/auth/login';
import logout from '../admin-dashboard/src/pages/api/auth/logout';
import callback from '../admin-dashboard/src/pages/api/auth/callback';
import { auth0 } from '../admin-dashboard/src/lib/auth0';

jest.mock('../admin-dashboard/src/lib/auth0', () => ({
  auth0: {
    handleLogin: jest.fn(async () => {}),
    handleLogout: jest.fn(async () => {}),
    handleCallback: jest.fn(async () => {}),
  },
}));

describe('auth routes', () => {
  const req = {} as NextApiRequest;
  const res = {} as NextApiResponse;

  it('calls handleLogin', async () => {
    await login(req, res);
    expect(auth0.handleLogin).toHaveBeenCalledWith(req, res);
  });

  it('calls handleLogout', async () => {
    await logout(req, res);
    expect(auth0.handleLogout).toHaveBeenCalledWith(req, res);
  });

  it('calls handleCallback', async () => {
    await callback(req, res);
    expect(auth0.handleCallback).toHaveBeenCalledWith(req, res);
  });
});
