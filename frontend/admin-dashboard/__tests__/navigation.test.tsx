import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Router from 'next-router-mock';
import { RouterContext } from 'next/dist/shared/lib/router-context.shared-runtime';
import AdminLayout from '../src/layouts/AdminLayout';

function renderWithRouter(ui: React.ReactElement) {
  return render(
    <RouterContext.Provider value={Router}>{ui}</RouterContext.Provider>
  );
}

test('navigates to Heatmap page when link clicked', async () => {
  Router.setCurrentUrl('/dashboard');
  renderWithRouter(
    <AdminLayout>
      <div>Home</div>
    </AdminLayout>
  );
  await userEvent.click(screen.getByText('Heatmap'));
  expect(Router).toMatchObject({ pathname: '/dashboard/heatmap' });
});
