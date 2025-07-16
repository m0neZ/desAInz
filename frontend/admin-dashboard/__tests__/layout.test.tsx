import { render, screen } from '@testing-library/react';
import { axe } from 'jest-axe';
import RootLayout from '../app/layout';

test('renders children inside layout', async () => {
  const originalError = console.error;
  console.error = jest.fn();
  const { container } = render(
    <RootLayout>
      <div>Child</div>
    </RootLayout>
  );
  expect(screen.getByText('Child')).toBeInTheDocument();
  const results = await axe(container);
  expect(results).toHaveNoViolations();
  console.error = originalError;
});
