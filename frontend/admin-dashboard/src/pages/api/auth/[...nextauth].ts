import NextAuth, { type NextAuthOptions } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        username: { label: 'Username', type: 'text' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        const user = process.env.ADMIN_USER ?? 'admin';
        const pass = process.env.ADMIN_PASS ?? 'password';
        if (credentials?.username === user && credentials?.password === pass) {
          return { id: '1', name: 'Admin' };
        }
        return null;
      },
    }),
  ],
  session: { strategy: 'jwt' },
  secret: process.env.NEXTAUTH_SECRET ?? 'changeme',
};

export default NextAuth(authOptions);
