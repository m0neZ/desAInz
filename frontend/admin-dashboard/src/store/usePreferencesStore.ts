// @flow
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface PreferencesState {
  notifyOnFail: boolean;
  toggleNotify: () => void;
}

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set) => ({
      notifyOnFail: false,
      toggleNotify: () => set((s) => ({ notifyOnFail: !s.notifyOnFail })),
    }),
    { name: 'preferences-store' }
  )
);
