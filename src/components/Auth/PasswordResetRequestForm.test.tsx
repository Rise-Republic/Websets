import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PasswordResetRequestForm from './PasswordResetRequestForm';
import * as useAuthHook from '@/hooks/useAuth';

jest.mock('@/hooks/useAuth');
const mockUseAuth = useAuthHook as jest.Mocked<typeof useAuthHook>;

describe('PasswordResetRequestForm', () => {
  const mockRequest = jest.fn();

  beforeEach(() => {
    mockUseAuth.useAuth.mockReturnValue({
      requestPasswordReset: mockRequest,
    } as any);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('submits email', async () => {
    const user = userEvent.setup();
    render(<PasswordResetRequestForm />);

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.click(screen.getByRole('button', { name: /send reset link/i }));

    expect(mockRequest).toHaveBeenCalledWith('test@example.com');
  });
});
