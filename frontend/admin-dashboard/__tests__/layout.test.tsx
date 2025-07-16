import { render, screen } from '@testing-library/react';
import RootLayout from '../app/layout';

test('renders children inside layout', () => {
  const originalError = console.error;
  console.error = jest.fn();
  render(
    <RootLayout>
      <div>Child</div>
    </RootLayout>,
    { container: document.documentElement }
  );
  expect(screen.getByText('Child')).toBeInTheDocument();
  console.error = originalError;
});
