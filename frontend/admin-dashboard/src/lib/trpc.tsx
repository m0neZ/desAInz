// @flow
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      cacheTime: 1000 * 60 * 60, // 60 minutes
      staleTime: 1000 * 60 * 10, // 10 minutes
    },
  },
});

export function TrpcProvider({ children }: { children: ReactNode }) {
  'use client';
  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
