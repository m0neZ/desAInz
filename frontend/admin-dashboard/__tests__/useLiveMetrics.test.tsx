import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { useLiveMetrics } from '../src/hooks/useLiveMetrics';

class WebSocketMock {
  url: string;
  onmessage: ((ev: MessageEvent) => void) | null = null;
  onerror: ((ev: Event) => void) | null = null;
  close = jest.fn();

  constructor(url: string) {
    this.url = url;
  }

  sendMessage(data: string) {
    if (this.onmessage) {
      this.onmessage({ data } as MessageEvent);
    }
  }

  triggerError(event: Event) {
    if (this.onerror) {
      this.onerror(event);
    }
  }
}

describe('useLiveMetrics', () => {
  let originalWebSocket: typeof WebSocket;
  let wsInstance: WebSocketMock;

  beforeEach(() => {
    originalWebSocket = global.WebSocket;
    // @ts-expect-error override
    global.WebSocket = jest.fn((url: string) => {
      wsInstance = new WebSocketMock(url);
      return wsInstance as unknown as WebSocket;
    });
  });

  afterEach(() => {
    global.WebSocket = originalWebSocket;
    jest.restoreAllMocks();
  });

  function TestComponent() {
    const metrics = useLiveMetrics();
    return (
      <div data-testid="metrics">
        {metrics ? JSON.stringify(metrics) : 'null'}
      </div>
    );
  }

  test('updates metrics on WebSocket messages', () => {
    render(<TestComponent />);
    expect(global.WebSocket).toHaveBeenCalled();

    act(() => {
      wsInstance.sendMessage('{"cpu_percent": 5}');
    });
    expect(screen.getByTestId('metrics')).toHaveTextContent(
      '{"cpu_percent":5}'
    );

    act(() => {
      wsInstance.sendMessage('bad json');
    });
    // state should remain unchanged
    expect(screen.getByTestId('metrics')).toHaveTextContent(
      '{"cpu_percent":5}'
    );

    act(() => {
      wsInstance.triggerError(new Event('error'));
    });
    // no crash, state unchanged
    expect(screen.getByTestId('metrics')).toHaveTextContent(
      '{"cpu_percent":5}'
    );
  });

  test('cleans up WebSocket on unmount', () => {
    const { unmount } = render(<TestComponent />);
    act(() => {
      wsInstance.sendMessage('{"memory_mb": 10}');
    });
    expect(screen.getByTestId('metrics')).toHaveTextContent('{"memory_mb":10}');
    unmount();
    expect(wsInstance.close).toHaveBeenCalled();
  });
});
