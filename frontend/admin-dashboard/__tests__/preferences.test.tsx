import { fireEvent, render, screen } from '@testing-library/react';
import PreferencesPage from '../src/pages/dashboard/preferences';

test('toggles notification setting', () => {
  render(<PreferencesPage />);
  const checkbox = screen.getByRole('checkbox');
  expect(checkbox).toBeChecked();
  fireEvent.click(checkbox);
  expect(checkbox).not.toBeChecked();
});
