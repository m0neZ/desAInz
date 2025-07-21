import '@testing-library/jest-dom';

// Provide a stub canvas implementation for Chart.js
HTMLCanvasElement.prototype.getContext =
  HTMLCanvasElement.prototype.getContext ||
  (() => ({
    fillRect: () => {},
    clearRect: () => {},
    getImageData: () => ({ data: [] }),
    putImageData: () => {},
    createImageData: () => [],
    setTransform: () => {},
    drawImage: () => {},
    save: () => {},
    fillText: () => {},
    restore: () => {},
    beginPath: () => {},
    moveTo: () => {},
    lineTo: () => {},
    closePath: () => {},
    stroke: () => {},
    translate: () => {},
    scale: () => {},
    rotate: () => {},
    arc: () => {},
    fill: () => {},
    measureText: () => ({ width: 0 }),
    transform: () => {},
    rect: () => {},
    clip: () => {},
  }));

global.ResizeObserver =
  global.ResizeObserver ||
  class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };

// Fail tests if any console warnings or errors are logged.
beforeAll(() => {
  jest.spyOn(console, 'error').mockImplementation((...args) => {
    const msg = args.join(' ');
    if (msg.includes('not wrapped in act')) {
      return;
    }
    throw new Error(`console.error: ${msg}`);
  });
  jest.spyOn(console, 'warn').mockImplementation((...args) => {
    throw new Error(`console.warn: ${args.join(' ')}`);
  });
});

afterAll(() => {
  (console.error as jest.Mock).mockRestore();
  (console.warn as jest.Mock).mockRestore();
});
