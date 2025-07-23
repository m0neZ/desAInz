import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface StoreState {
  isAuthenticated: boolean;
  notifyOnFail: boolean;
  setAuthenticated: (auth: boolean) => void;
  toggleNotify: () => void;
}

export const useStore = create<StoreState>()(
  persist(
    (set) => ({
      isAuthenticated: false,
      notifyOnFail: false,
      setAuthenticated: (auth: boolean) => set({ isAuthenticated: auth }),
      toggleNotify: () => set((s) => ({ notifyOnFail: !s.notifyOnFail })),
    }),
    { name: 'admin-dashboard-store' }
  )
);
