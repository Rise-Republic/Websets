import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { AuthContext } from '../../hooks/useAuth';

// Mock user data
export const mockUser = {
  id: '1',
  email: 'test@example.com',
  fullName: 'Test User',
  isActive: true,
  createdAt: '2023-01-01T00:00:00.000Z'
};

// Mock auth context values
export const createMockAuthContext = (overrides = {}) => ({
  user: null,
  isLoading: false,
  isAuthenticated: false,
  login: jest.fn(),
  register: jest.fn(),
  logout: jest.fn(),
  requestPasswordReset: jest.fn(),
  confirmPasswordReset: jest.fn(),
  error: null,
  ...overrides,
});

// Custom render function with providers
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  authContext?: any;
}

export const renderWithProviders = (
  ui: ReactElement,
  options: CustomRenderOptions = {}
) => {
  const { authContext = createMockAuthContext(), ...renderOptions } = options;

  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <AuthContext.Provider value={authContext}>
      {children}
    </AuthContext.Provider>
  );

  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

// Re-export everything from React Testing Library
export * from '@testing-library/react';
export { renderWithProviders as render };

// Placeholder test so Jest treats this file as a test suite without failing
test('utils placeholder', () => {});
