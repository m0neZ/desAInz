import { render, screen } from '@testing-library/react';
import AuthButton from '../admin-dashboard/src/components/AuthButton';
import { __setUser } from '../admin-dashboard/__mocks__/@auth0/nextjs-auth0/client';

describe('AuthButton', () => {
  it('shows login link when unauthenticated', () => {
    __setUser(null);
    render(<AuthButton />);
    const link = screen.getByRole('link', { name: /login/i });
    expect(link).toHaveAttribute('href', '/api/auth/login');
  });

  it('shows logout link when authenticated', () => {
    __setUser({ name: 'test' });
    render(<AuthButton />);
    const link = screen.getByRole('link', { name: /logout/i });
    expect(link).toHaveAttribute('href', '/api/auth/logout');
  });
});
