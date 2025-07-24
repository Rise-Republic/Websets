import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LoginForm from './LoginForm';
import * as useAuthHook from '@/hooks/useAuth';

jest.mock('@/hooks/useAuth');
const mockUseAuth = useAuthHook as jest.Mocked<typeof useAuthHook>;

describe('LoginForm', () => {
  const mockLogin = jest.fn();

  beforeEach(() => {
    mockUseAuth.useAuth.mockReturnValue({
      login: mockLogin,
      logout: jest.fn(),
      isLoading: false,
      isAuthenticated: false,
      user: null,
    } as any);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders sign in button', () => {
    render(<LoginForm />);
    expect(screen.getByRole('button', { name: /sign in with auth0/i })).toBeInTheDocument();
  });

  test('calls login when button is clicked', async () => {
    const user = userEvent.setup();
    render(<LoginForm />);
    await user.click(screen.getByRole('button', { name: /sign in with auth0/i }));
    expect(mockLogin).toHaveBeenCalledTimes(1);
  });
});
