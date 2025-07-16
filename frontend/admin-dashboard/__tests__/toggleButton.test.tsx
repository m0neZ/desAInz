import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ToggleButton } from '../src/components/ToggleButton';

test('toggles label when clicked', async () => {
  render(<ToggleButton />);
  const button = screen.getByTestId('toggle-button');
  expect(button).toHaveTextContent('Off');
  await userEvent.click(button);
  expect(button).toHaveTextContent('On');
  await userEvent.click(button);
  expect(button).toHaveTextContent('Off');
});
