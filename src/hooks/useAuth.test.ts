import { renderHook, act, waitFor } from '@testing-library/react';
import { useAuth, useAuthProvider } from './useAuth';
import * as apiService from '@/services/api';

// Mock the API service
jest.mock('@/services/api');
const mockApiService = apiService as jest.Mocked<typeof apiService>;

// Mock API service default export
const mockDefaultApiService = {
  login: jest.fn(),
  register: jest.fn(),
  logout: jest.fn(),
  getCurrentUser: jest.fn(),
  isAuthenticated: jest.fn(),
  passwordResetRequest: jest.fn(),
  passwordResetConfirm: jest.fn(),
};

// Set up the default export mock
(apiService as any).default = mockDefaultApiService;

describe('useAuthProvider', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockDefaultApiService.isAuthenticated.mockReturnValue(false);
  });

  test('initializes with correct default state', async () => {
    const { result } = renderHook(() => useAuthProvider());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toBe(null);
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.error).toBe(null);
  });

  test('checks for existing authentication on mount', async () => {
    const mockUser = { id: '1', email: 'test@example.com', fullName: 'Test User' };
    mockDefaultApiService.isAuthenticated.mockReturnValue(true);
    mockDefaultApiService.getCurrentUser.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuthProvider());

    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockDefaultApiService.getCurrentUser).toHaveBeenCalledTimes(1);
  });

  test('handles expired token on mount', async () => {
    mockDefaultApiService.isAuthenticated.mockReturnValue(true);
    mockDefaultApiService.getCurrentUser.mockRejectedValue(new Error('Token expired'));

    const { result } = renderHook(() => useAuthProvider());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toBe(null);
    expect(result.current.isAuthenticated).toBe(false);
    expect(mockDefaultApiService.logout).toHaveBeenCalledTimes(1);
  });

  test('login success', async () => {
    const mockUser = { id: '1', email: 'test@example.com', fullName: 'Test User' };
    mockDefaultApiService.login.mockResolvedValue(undefined);
    mockDefaultApiService.getCurrentUser.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuthProvider());

    await act(async () => {
      await result.current.login('test@example.com', 'password');
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.error).toBe(null);
    expect(result.current.isLoading).toBe(false);
    expect(mockDefaultApiService.login).toHaveBeenCalledWith('test@example.com', 'password');
  });

  test('login failure', async () => {
    const errorMessage = 'Invalid credentials';
    mockDefaultApiService.login.mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useAuthProvider());

    await act(async () => {
      try {
        await result.current.login('test@example.com', 'wrongpassword');
      } catch (err) {
        // Expected to throw
      }
    });

    expect(result.current.user).toBe(null);
    expect(result.current.error).toBe(errorMessage);
    expect(result.current.isLoading).toBe(false);
  });

  test('login fails if fetching current user throws', async () => {
    mockDefaultApiService.login.mockResolvedValue(undefined);
    mockDefaultApiService.getCurrentUser.mockRejectedValue(new Error('fetch error'));

    const { result } = renderHook(() => useAuthProvider());

    await act(async () => {
      await expect(result.current.login('test@example.com', 'password')).rejects.toThrow('fetch error');
    });

    expect(result.current.user).toBe(null);
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.error).toBe('fetch error');
    expect(result.current.isLoading).toBe(false);
  });

  test('register success and auto-login', async () => {
    const mockUser = { id: '1', email: 'test@example.com', fullName: 'Test User' };
    mockDefaultApiService.register.mockResolvedValue(mockUser);
    mockDefaultApiService.login.mockResolvedValue(undefined);
    mockDefaultApiService.getCurrentUser.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuthProvider());

    await act(async () => {
      await result.current.register('test@example.com', 'password', 'Test User');
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.error).toBe(null);
    expect(result.current.isLoading).toBe(false);
    expect(mockDefaultApiService.register).toHaveBeenCalledWith('test@example.com', 'password', 'Test User');
    expect(mockDefaultApiService.login).toHaveBeenCalledWith('test@example.com', 'password');
  });

  test('register failure', async () => {
    const errorMessage = 'Email already exists';
    mockDefaultApiService.register.mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useAuthProvider());

    await act(async () => {
      try {
        await result.current.register('test@example.com', 'password', 'Test User');
      } catch (err) {
        // Expected to throw
      }
    });

    expect(result.current.user).toBe(null);
    expect(result.current.error).toBe(errorMessage);
    expect(result.current.isLoading).toBe(false);
  });

  test('logout clears user state', async () => {
    const mockUser = { id: '1', email: 'test@example.com', fullName: 'Test User' };
    
    // Set up initial authenticated state
    mockDefaultApiService.isAuthenticated.mockReturnValue(true);
    mockDefaultApiService.getCurrentUser.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuthProvider());

    // Wait for initial auth check
    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser);
    });

    // Logout
    act(() => {
      result.current.logout();
    });

    expect(result.current.user).toBe(null);
    expect(result.current.error).toBe(null);
    expect(mockDefaultApiService.logout).toHaveBeenCalledTimes(1);
  });

  test('logout after login clears authentication', async () => {
    const mockUser = { id: '1', email: 'test@example.com', fullName: 'Test User' };
    mockDefaultApiService.login.mockResolvedValue(undefined);
    mockDefaultApiService.getCurrentUser.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuthProvider());

    await act(async () => {
      await result.current.login('test@example.com', 'password');
    });

    act(() => {
      result.current.logout();
    });

    expect(result.current.user).toBe(null);
    expect(result.current.isAuthenticated).toBe(false);
    expect(mockDefaultApiService.logout).toHaveBeenCalledTimes(1);
  });

  test('isAuthenticated works correctly', async () => {
    mockDefaultApiService.isAuthenticated.mockReturnValue(true);
    
    const { result } = renderHook(() => useAuthProvider());

    // Initially false because user is null
    expect(result.current.isAuthenticated).toBe(false);

    // Mock a successful login
    const mockUser = { id: '1', email: 'test@example.com', fullName: 'Test User' };
    mockDefaultApiService.login.mockResolvedValue(undefined);
    mockDefaultApiService.getCurrentUser.mockResolvedValue(mockUser);

    await act(async () => {
      await result.current.login('test@example.com', 'password');
    });

    expect(result.current.isAuthenticated).toBe(true);
  });

  test('request password reset', async () => {
    mockDefaultApiService.passwordResetRequest.mockResolvedValue({ message: 'ok', token: 't' });

    const { result } = renderHook(() => useAuthProvider());

    await act(async () => {
      await result.current.requestPasswordReset('test@example.com');
    });

    expect(mockDefaultApiService.passwordResetRequest).toHaveBeenCalledWith('test@example.com');
    expect(result.current.error).toBe(null);
  });

  test('confirm password reset', async () => {
    mockDefaultApiService.passwordResetConfirm.mockResolvedValue({ message: 'ok' });

    const { result } = renderHook(() => useAuthProvider());

    await act(async () => {
      await result.current.confirmPasswordReset('token', 'newpass');
    });

    expect(mockDefaultApiService.passwordResetConfirm).toHaveBeenCalledWith('token', 'newpass');
    expect(result.current.error).toBe(null);
  });
});

describe('useAuth', () => {
  test('throws error when used outside AuthProvider', () => {
    // Mock console.error to avoid cluttering test output
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    
    expect(() => {
      renderHook(() => useAuth());
    }).toThrow('useAuth must be used within AuthProvider');

    consoleSpy.mockRestore();
  });
});
