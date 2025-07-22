import { render, screen } from '@testing-library/react';
import Router from 'next-router-mock';
import { RouterContext } from 'next/dist/shared/lib/router-context.shared-runtime';
import RootLayout from '../app/layout';

test('renders children inside layout', () => {
  const originalError = console.error;
  console.error = jest.fn();
  render(
    <RouterContext.Provider value={Router}>
      <RootLayout>
        <div>Child</div>
      </RootLayout>
    </RouterContext.Provider>,
    { container: document.documentElement }
  );
  expect(screen.getByText('Child')).toBeInTheDocument();
  console.error = originalError;
});
