import { useUserStore } from '../src/store/useUserStore';
import { usePreferenceStore } from '../src/store/usePreferenceStore';

describe('stores', () => {
  beforeEach(() => {
    localStorage.clear();
    useUserStore.setState({ token: null, refreshToken: null });
    usePreferenceStore.setState({ notifyFail: false });
  });

  test('user store persists tokens', () => {
    useUserStore.getState().setTokens('t', 'r');
    expect(useUserStore.getState().token).toBe('t');
    expect(localStorage.getItem('token')).toBe('t');
    useUserStore.getState().clear();
    expect(useUserStore.getState().token).toBeNull();
    expect(localStorage.getItem('token')).toBeNull();
  });

  test('preference store persists notify flag', () => {
    usePreferenceStore.getState().setNotifyFail(true);
    expect(usePreferenceStore.getState().notifyFail).toBe(true);
    expect(localStorage.getItem('notifyFail')).toBe('true');
  });
});
