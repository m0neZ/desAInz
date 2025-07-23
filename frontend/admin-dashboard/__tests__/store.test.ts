import { act } from '@testing-library/react';
import { useUserStore } from '../src/store/useUserStore';
import { usePreferencesStore } from '../src/store/usePreferencesStore';

test('updates auth state', () => {
  expect(useUserStore.getState().isAuthenticated).toBe(false);
  act(() => {
    useUserStore.getState().setAuthenticated(true);
  });
  expect(useUserStore.getState().isAuthenticated).toBe(true);
});

test('toggles preference', () => {
  expect(usePreferencesStore.getState().notifyOnFail).toBe(false);
  act(() => {
    usePreferencesStore.getState().toggleNotify();
  });
  expect(usePreferencesStore.getState().notifyOnFail).toBe(true);
});
