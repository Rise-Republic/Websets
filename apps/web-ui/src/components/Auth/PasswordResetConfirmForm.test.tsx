import React from 'react';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PasswordResetConfirmForm from './PasswordResetConfirmForm';
import { useAuth } from '@/hooks/useAuth';

jest.mock('@/hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

describe('PasswordResetConfirmForm', () => {
  const mockConfirm = jest.fn();

  beforeEach(() => {
    mockUseAuth.mockReturnValue({
      confirmPasswordReset: mockConfirm,
    } as any);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('submits data', async () => {
    const user = userEvent.setup();
    render(<PasswordResetConfirmForm />);

    await user.type(screen.getByLabelText(/token/i), 'tok');
    await user.type(screen.getByLabelText(/new password/i), 'password');
    await user.type(screen.getByLabelText(/confirm password/i), 'password');
    await act(async () => {
      await user.click(
        screen.getByRole('button', { name: /reset password/i })
      );
    });

    expect(mockConfirm).toHaveBeenCalledWith('tok', 'password');
  });
});
