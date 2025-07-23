// @flow
import { create } from 'zustand';

export interface UserState {
  token: string | null;
  refreshToken: string | null;
  setTokens: (token: string, refreshToken: string) => void;
  clear: () => void;
}

function getInitialToken(key: string): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(key);
}

export const useUserStore = create<UserState>((set) => ({
  token: getInitialToken('token'),
  refreshToken: getInitialToken('refresh_token'),
  setTokens: (token: string, refreshToken: string) => {
    set({ token, refreshToken });
    if (typeof window !== 'undefined') {
      localStorage.setItem('token', token);
      localStorage.setItem('refresh_token', refreshToken);
    }
  },
  clear: () => {
    set({ token: null, refreshToken: null });
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
    }
  },
}));
