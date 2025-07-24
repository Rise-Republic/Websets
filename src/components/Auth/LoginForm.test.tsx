import React from 'react';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LoginForm from './LoginForm';
import { useAuth } from '@/hooks/useAuth';

jest.mock('@/hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

describe('LoginForm', () => {
  const mockLogin = jest.fn();

  beforeEach(() => {
    mockUseAuth.mockReturnValue({
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

  test.skip('renders sign in button', () => {
    render(<LoginForm />);
    expect(screen.getByRole('button', { name: /sign in with auth0/i })).toBeInTheDocument();
  });

  test.skip('calls login when button is clicked', async () => {
    const user = userEvent.setup();
    render(<LoginForm />);
    await act(async () => {
      await user.click(
        screen.getByRole('button', { name: /sign in with auth0/i })
      );
    });
    expect(mockLogin).toHaveBeenCalledTimes(1);
  });
});
