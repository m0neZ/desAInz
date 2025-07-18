import { act, render, screen } from '@testing-library/react';
import { changeLanguage } from '../src/i18n';
import { ToggleButton } from '../src/components/ToggleButton';

test('switches locale at runtime', async () => {
  render(<ToggleButton />);
  const button = screen.getByTestId('toggle-button');
  expect(button).toHaveTextContent('Off');
  await act(async () => {
    await changeLanguage('es');
  });
  expect(button).toHaveTextContent('Apagado');
  await act(async () => {
    await changeLanguage('en');
  });
});
