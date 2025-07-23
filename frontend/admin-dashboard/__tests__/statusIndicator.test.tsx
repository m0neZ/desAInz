import { render, act } from '@testing-library/react';
import StatusIndicator from '../src/components/StatusIndicator';

(global.fetch as jest.Mock) = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ api: 'ok' }),
  })
) as jest.Mock;

afterEach(() => {
  (global.fetch as jest.Mock).mockClear();
});

test('pauses polling when tab hidden', () => {
  jest.useFakeTimers();
  render(<StatusIndicator />);
  const startCount = (global.fetch as jest.Mock).mock.calls.length;
  act(() => {
    jest.advanceTimersByTime(5000);
  });
  expect((global.fetch as jest.Mock).mock.calls.length).toBe(startCount + 1);

  Object.defineProperty(document, 'visibilityState', {
    configurable: true,
    get: () => 'hidden',
  });
  act(() => {
    document.dispatchEvent(new Event('visibilitychange'));
    jest.advanceTimersByTime(10000);
  });
  expect((global.fetch as jest.Mock).mock.calls.length).toBe(startCount + 1);

  Object.defineProperty(document, 'visibilityState', {
    configurable: true,
    get: () => 'visible',
  });
  act(() => {
    document.dispatchEvent(new Event('visibilitychange'));
    jest.advanceTimersByTime(5000);
  });
  expect((global.fetch as jest.Mock).mock.calls.length).toBeGreaterThan(startCount + 1);
  jest.useRealTimers();
});
