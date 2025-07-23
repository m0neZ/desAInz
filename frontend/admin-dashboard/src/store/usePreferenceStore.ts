// @flow
import { create } from 'zustand';

export interface PreferenceState {
  notifyFail: boolean;
  setNotifyFail: (value: boolean) => void;
}

function getInitialBoolean(key: string): boolean {
  if (typeof window === 'undefined') return false;
  return localStorage.getItem(key) === 'true';
}

export const usePreferenceStore = create<PreferenceState>((set) => ({
  notifyFail: getInitialBoolean('notifyFail'),
  setNotifyFail: (value: boolean) => {
    set({ notifyFail: value });
    if (typeof window !== 'undefined') {
      localStorage.setItem('notifyFail', String(value));
    }
  },
}));
