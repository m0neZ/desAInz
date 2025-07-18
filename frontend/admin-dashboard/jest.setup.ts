import '@testing-library/jest-dom';
import './src/i18n';

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
