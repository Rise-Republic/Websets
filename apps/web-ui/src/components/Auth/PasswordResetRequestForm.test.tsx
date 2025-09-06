import React from 'react';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PasswordResetRequestForm from './PasswordResetRequestForm';
import { useAuth } from '@/hooks/useAuth';

jest.mock('@/hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

describe('PasswordResetRequestForm', () => {
  const mockRequest = jest.fn();

  beforeEach(() => {
    mockUseAuth.mockReturnValue({
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
    await act(async () => {
      await user.click(
        screen.getByRole('button', { name: /send reset link/i })
      );
    });

    expect(mockRequest).toHaveBeenCalledWith('test@example.com');
  });
});
