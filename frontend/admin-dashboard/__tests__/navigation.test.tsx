import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Router from 'next-router-mock';
import { RouterContext } from 'next/dist/shared/lib/router-context.shared-runtime';
import AdminLayout from '../src/layouts/AdminLayout';

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key.charAt(0).toUpperCase() + key.slice(1),
  }),
}));

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

test('navigates to Roles page when link clicked', async () => {
  Router.setCurrentUrl('/dashboard');
  renderWithRouter(
    <AdminLayout>
      <div>Home</div>
    </AdminLayout>
  );
  await userEvent.click(screen.getByText('Roles'));
  expect(Router).toMatchObject({ pathname: '/dashboard/roles' });
});

test('navigates to Maintenance page when link clicked', async () => {
  Router.setCurrentUrl('/dashboard');
  renderWithRouter(
    <AdminLayout>
      <div>Home</div>
    </AdminLayout>
  );
  await userEvent.click(screen.getByText('Maintenance'));
  expect(Router).toMatchObject({ pathname: '/dashboard/maintenance' });
});

test('shows Zazzle link when flag enabled', () => {
  process.env.NEXT_PUBLIC_ENABLE_ZAZZLE = 'true';
  Router.setCurrentUrl('/dashboard');
  renderWithRouter(
    <AdminLayout>
      <div>Home</div>
    </AdminLayout>
  );
  expect(screen.getByText('Zazzle')).toBeInTheDocument();
  delete process.env.NEXT_PUBLIC_ENABLE_ZAZZLE;
});
