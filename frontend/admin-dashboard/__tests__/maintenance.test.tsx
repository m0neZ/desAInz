import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MaintenancePage from '../src/pages/dashboard/maintenance';

global.fetch = jest.fn(() =>
  Promise.resolve({ ok: true, json: () => Promise.resolve({ status: 'ok' }) })
) as jest.Mock;

test('runs maintenance when triggered', async () => {
  render(<MaintenancePage />);
  await userEvent.click(screen.getByTestId('maintenance-button'));
  expect(global.fetch).toHaveBeenCalledWith('/api/maintenance', {
    method: 'POST',
  });
  expect(await screen.findByTestId('maintenance-status')).toHaveTextContent(
    'done'
  );
});
