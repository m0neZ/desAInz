// @flow
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      cacheTime: 1000 * 60 * 30, // 30 minutes
      staleTime: 1000 * 60 * 5, // 5 minutes
    },
  },
});
