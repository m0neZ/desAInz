// @flow
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      cacheTime: 1000 * 60 * 30, // 30 minutes
      staleTime: 1000 * 60 * 5, // 5 minutes
    },
  },
});

export function TrpcProvider({ children }: { children: ReactNode }) {
  'use client';
  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
