import { render, screen, waitFor, act } from '@testing-library/react';
import LatencyIndicator from '../src/components/LatencyIndicator';

global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ average_seconds: 7200 }),
  })
) as jest.Mock;

test('displays latency value', async () => {
  render(<LatencyIndicator />);
  await waitFor(() => screen.getByTestId('latency-indicator'));
  expect(
    screen.getByText(/Avg time from signal to publish/)
  ).toBeInTheDocument();
});

test('pauses polling when tab hidden', () => {
  jest.useFakeTimers();
  render(<LatencyIndicator />);
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
    jest.advanceTimersByTime(5000);
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
