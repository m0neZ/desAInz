import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import Router from 'next-router-mock';
import { RouterContext } from 'next/dist/shared/lib/router-context.shared-runtime';
import { ToggleButton } from '../src/components/ToggleButton';
import { I18nProvider } from '../src/i18n';

function renderWithRouter(ui: React.ReactElement) {
  return render(
    <RouterContext.Provider value={Router}>
      <I18nProvider>{ui}</I18nProvider>
    </RouterContext.Provider>
  );
}

test('loads translations based on router locale', async () => {
  Router.locale = 'es';
  const { unmount } = renderWithRouter(<ToggleButton />);
  await waitFor(() =>
    expect(screen.getByTestId('toggle-button')).toHaveTextContent('Apagado')
  );
  unmount();
  Router.locale = 'en';
  renderWithRouter(<ToggleButton />);
  await waitFor(() =>
    expect(screen.getByTestId('toggle-button')).toHaveTextContent('Off')
  );
});
