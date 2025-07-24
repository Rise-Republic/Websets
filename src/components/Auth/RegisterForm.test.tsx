import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RegisterForm from './RegisterForm';
import * as useAuthHook from '@/hooks/useAuth';

jest.mock('@/hooks/useAuth');
const mockUseAuth = useAuthHook as jest.Mocked<typeof useAuthHook>;

describe('RegisterForm', () => {
  const mockRegister = jest.fn();

  beforeEach(() => {
    mockUseAuth.useAuth.mockReturnValue({
      register: mockRegister,
    } as any);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('submits form data', async () => {
    const user = userEvent.setup();
    render(<RegisterForm />);

    await user.type(screen.getByLabelText(/full name/i), 'Test User');
    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'password');
    await user.type(screen.getByLabelText(/confirm password/i), 'password');

    await user.click(screen.getByRole('button', { name: /register/i }));

    expect(mockRegister).toHaveBeenCalledWith('test@example.com', 'password', 'Test User');
  });
});
