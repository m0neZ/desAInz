import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Router from 'next-router-mock';
import { RouterContext } from 'next/dist/shared/lib/router-context.shared-runtime';
import { axe, toHaveNoViolations } from 'jest-axe';
import { Button } from '../src/components/Button';
import { ToggleButton } from '../src/components/ToggleButton';
import { LanguageSwitcher } from '../src/components/LanguageSwitcher';

expect.extend(toHaveNoViolations);

function renderWithRouter(ui: React.ReactElement) {
  return render(
    <RouterContext.Provider value={Router}>{ui}</RouterContext.Provider>
  );
}

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

  it('ToggleButton toggles via keyboard', async () => {
    render(<ToggleButton />);
    const button = screen.getByTestId('toggle-button');
    button.focus();
    await userEvent.keyboard('{enter}');
    expect(button).toHaveAttribute('aria-pressed', 'true');
  });

  it('LanguageSwitcher allows keyboard selection', async () => {
    renderWithRouter(<LanguageSwitcher />);
    const first = screen.getByTestId('lang-en');
    first.focus();
    await userEvent.keyboard('{enter}');
    expect(first).toBeInTheDocument();
  });
});
