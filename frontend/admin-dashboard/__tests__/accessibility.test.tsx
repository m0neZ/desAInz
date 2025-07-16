import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { Button } from '../src/components/Button';
import { ToggleButton } from '../src/components/ToggleButton';

expect.extend(toHaveNoViolations);

describe('accessibility checks', () => {
  it('Button has no a11y violations', async () => {
    const { container } = render(<Button ariaLabel="submit">Click</Button>);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('ToggleButton has no a11y violations', async () => {
    const { container } = render(<ToggleButton />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
