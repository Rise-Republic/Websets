import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';

export const mockUser = {
  id: '1',
  email: 'test@example.com',
  fullName: 'Test User',
  isActive: true,
  createdAt: '2023-01-01T00:00:00.000Z',
};

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {}

export const renderWithProviders = (
  ui: ReactElement,
  options: CustomRenderOptions = {}
) => render(ui, options);

export * from '@testing-library/react';
export { renderWithProviders as render };

test('utils placeholder', () => {});
