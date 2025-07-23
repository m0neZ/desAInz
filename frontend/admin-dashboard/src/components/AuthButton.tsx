// @flow
import Link from 'next/link';
import { useUser } from '@auth0/nextjs-auth0/client';

export default function AuthButton() {
  const { user, isLoading } = useUser();
  if (isLoading) {
    return null;
  }
  if (user) {
    return (
      <Link href="/api/auth/logout" aria-label="Logout" className="ml-auto">
        Logout
      </Link>
    );
  }
  return (
    <Link href="/api/auth/login" aria-label="Login" className="ml-auto">
      Login
    </Link>
  );
}
