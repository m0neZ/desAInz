import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PaginationControls from '../admin-dashboard/src/components/PaginationControls';
import { ToggleButton } from '../admin-dashboard/src/components/ToggleButton';

test('pagination controls keyboard navigation', async () => {
  const user = userEvent.setup();
  const handler = jest.fn();
  render(
    <PaginationControls page={2} total={10} limit={1} onPageChange={handler} />
  );
  const prev = screen.getByRole('button', { name: /previous page/i });
  prev.focus();
  await user.keyboard('{Enter}');
  expect(handler).toHaveBeenCalled();
});

test('toggle button has accessible name', () => {
  render(<ToggleButton />);
  const btn = screen.getByRole('button', { name: /toggle/i });
  expect(btn).toBeInTheDocument();
});
