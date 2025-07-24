import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PasswordResetConfirmForm from './PasswordResetConfirmForm';
import * as useAuthHook from '@/hooks/useAuth';

jest.mock('@/hooks/useAuth');
const mockUseAuth = useAuthHook as jest.Mocked<typeof useAuthHook>;

describe('PasswordResetConfirmForm', () => {
  const mockConfirm = jest.fn();

  beforeEach(() => {
    mockUseAuth.useAuth.mockReturnValue({
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
    await user.click(screen.getByRole('button', { name: /reset password/i }));

    expect(mockConfirm).toHaveBeenCalledWith('tok', 'password');
  });
});
