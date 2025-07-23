// @flow
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface UserState {
  isAuthenticated: boolean;
  setAuthenticated: (auth: boolean) => void;
}

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      isAuthenticated: false,
      setAuthenticated: (auth: boolean) => set({ isAuthenticated: auth }),
    }),
    { name: 'user-store' }
  )
);
