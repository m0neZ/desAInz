import React from 'react';
import { render, screen, act } from '@testing-library/react';

class WebSocketMock {
  url: string;
  onmessage: ((ev: MessageEvent) => void) | null = null;
  onerror: ((ev: Event) => void) | null = null;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  close = jest.fn();

  constructor(url: string) {
    this.url = url;
  }

  sendMessage(data: string) {
    if (this.onmessage) {
      this.onmessage({ data } as MessageEvent);
    }
  }

  open() {
    if (this.onopen) {
      this.onopen();
    }
  }

  triggerClose() {
    if (this.onclose) {
      this.onclose();
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
  const connections: WebSocketMock[] = [];
  let TestComponent: React.FC;

  beforeEach(() => {
    originalWebSocket = global.WebSocket;
    // @ts-expect-error override
    global.WebSocket = jest.fn((url: string) => {
      wsInstance = new WebSocketMock(url);
      connections.push(wsInstance);
      return wsInstance as unknown as WebSocket;
    });
    process.env.NEXT_PUBLIC_WS_MAX_RETRIES = '2';
    const { useLiveMetrics } = require('../src/hooks/useLiveMetrics');
    TestComponent = function TestComponent() {
      const metrics = useLiveMetrics();
      return (
        <div data-testid="metrics">
          {metrics ? JSON.stringify(metrics) : 'null'}
        </div>
      );
    };
    connections.length = 0;
  });

  afterEach(() => {
    global.WebSocket = originalWebSocket;
    jest.restoreAllMocks();
  });

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

  test('reconnects when the socket closes unexpectedly', () => {
    jest.useFakeTimers();
    render(<TestComponent />);
    expect(global.WebSocket).toHaveBeenCalledTimes(1);

    act(() => {
      wsInstance.open();
      wsInstance.triggerClose();
    });
    act(() => {
      jest.advanceTimersByTime(2000);
      jest.runOnlyPendingTimers();
    });

    expect(global.WebSocket).toHaveBeenCalledTimes(2);

    act(() => {
      connections[1].open();
      wsInstance.triggerClose();
    });
    act(() => {
      jest.advanceTimersByTime(4000);
      jest.runOnlyPendingTimers();
    });

    expect(global.WebSocket).toHaveBeenCalledTimes(3);

    act(() => {
      connections[2].open();
      wsInstance.triggerClose();
    });
    act(() => {
      jest.advanceTimersByTime(8000);
      jest.runOnlyPendingTimers();
    });

    expect(global.WebSocket).toHaveBeenCalledTimes(3);
    jest.useRealTimers();
  });
});
