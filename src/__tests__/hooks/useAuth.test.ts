/**
 * Unit Tests for useAuth Hook
 * Testing authentication state management and operations
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuth } from '../../hooks/useAuth';

// Mock WorkOS
jest.mock('@workos-inc/authkit-react', () => ({
  useUser: jest.fn(),
  useAuth: jest.fn(),
  signIn: jest.fn(),
  signOut: jest.fn(),
}));

import { useUser, useAuth as useWorkOSAuth, signIn, signOut } from '@workos-inc/authkit-react';

const mockUseUser = useUser as jest.MockedFunction<typeof useUser>;
const mockUseWorkOSAuth = useWorkOSAuth as jest.MockedFunction<typeof useWorkOSAuth>;
const mockSignIn = signIn as jest.MockedFunction<typeof signIn>;
const mockSignOut = signOut as jest.MockedFunction<typeof signOut>;

// Mock fetch
global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

describe('useAuth Hook', () => {
  let queryClient: QueryClient;

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    jest.clearAllMocks();
  });

  it('returns authenticated user when logged in', async () => {
    const mockUser = {
      id: 'user-123',
      email: 'test@example.com',
      firstName: 'Test',
      lastName: 'User',
    };

    mockUseUser.mockReturnValue({
      user: mockUser,
      isLoading: false,
    });

    mockUseWorkOSAuth.mockReturnValue({
      getAccessToken: jest.fn().mockResolvedValue('mock-token'),
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual({
        id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
      });
      expect(result.current.isLoading).toBe(false);
    });
  });

  it('returns unauthenticated state when no user', () => {
    mockUseUser.mockReturnValue({
      user: null,
      isLoading: false,
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('returns loading state while authentication is pending', () => {
    mockUseUser.mockReturnValue({
      user: null,
      isLoading: true,
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('handles login successfully', async () => {
    mockSignIn.mockResolvedValue(undefined);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login();
    });

    expect(mockSignIn).toHaveBeenCalledTimes(1);
  });

  it('handles login errors', async () => {
    const loginError = new Error('Login failed');
    mockSignIn.mockRejectedValue(loginError);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      try {
        await result.current.login();
      } catch (error) {
        expect(error).toBe(loginError);
      }
    });

    expect(mockSignIn).toHaveBeenCalledTimes(1);
  });

  it('handles logout successfully', async () => {
    mockSignOut.mockResolvedValue(undefined);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.logout();
    });

    expect(mockSignOut).toHaveBeenCalledTimes(1);
  });

  it('gets access token when authenticated', async () => {
    const mockGetAccessToken = jest.fn().mockResolvedValue('access-token-123');
    
    mockUseUser.mockReturnValue({
      user: { id: 'user-123', email: 'test@example.com' },
      isLoading: false,
    });

    mockUseWorkOSAuth.mockReturnValue({
      getAccessToken: mockGetAccessToken,
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      const token = await result.current.getToken();
      expect(token).toBe('access-token-123');
    });

    expect(mockGetAccessToken).toHaveBeenCalledTimes(1);
  });

  it('returns null token when not authenticated', async () => {
    mockUseUser.mockReturnValue({
      user: null,
      isLoading: false,
    });

    mockUseWorkOSAuth.mockReturnValue({
      getAccessToken: jest.fn(),
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      const token = await result.current.getToken();
      expect(token).toBeNull();
    });
  });

  it('handles token refresh on expiry', async () => {
    const mockGetAccessToken = jest.fn()
      .mockResolvedValueOnce('expired-token')
      .mockResolvedValueOnce('new-token');

    mockUseUser.mockReturnValue({
      user: { id: 'user-123', email: 'test@example.com' },
      isLoading: false,
    });

    mockUseWorkOSAuth.mockReturnValue({
      getAccessToken: mockGetAccessToken,
    });

    // Mock API call that returns 401
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ error: 'Token expired' }),
    } as Response);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      const token = await result.current.getToken();
      expect(token).toBe('expired-token');
    });

    // Simulate token refresh
    await act(async () => {
      const newToken = await result.current.getToken();
      expect(newToken).toBe('new-token');
    });

    expect(mockGetAccessToken).toHaveBeenCalledTimes(2);
  });

  it('provides user permissions correctly', async () => {
    const mockUser = {
      id: 'user-123',
      email: 'admin@example.com',
      firstName: 'Admin',
      lastName: 'User',
      role: 'admin',
    };

    mockUseUser.mockReturnValue({
      user: mockUser,
      isLoading: false,
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.hasPermission('admin')).toBe(true);
      expect(result.current.hasPermission('user')).toBe(true);
      expect(result.current.hasPermission('super_admin')).toBe(false);
    });
  });

  it('handles authentication state changes', async () => {
    // Start unauthenticated
    mockUseUser.mockReturnValue({
      user: null,
      isLoading: false,
    });

    const { result, rerender } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(false);

    // Simulate login
    mockUseUser.mockReturnValue({
      user: { id: 'user-123', email: 'test@example.com' },
      isLoading: false,
    });

    rerender();

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });
  });

  it('clears user data on logout', async () => {
    // Start authenticated
    mockUseUser.mockReturnValue({
      user: { id: 'user-123', email: 'test@example.com' },
      isLoading: false,
    });

    mockSignOut.mockResolvedValue(undefined);

    const { result, rerender } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(true);

    // Perform logout
    await act(async () => {
      await result.current.logout();
    });

    // Simulate user being cleared
    mockUseUser.mockReturnValue({
      user: null,
      isLoading: false,
    });

    rerender();

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });
  });

  it('handles network errors during authentication', async () => {
    mockUseUser.mockReturnValue({
      user: { id: 'user-123', email: 'test@example.com' },
      isLoading: false,
    });

    const mockGetAccessToken = jest.fn().mockRejectedValue(new Error('Network error'));

    mockUseWorkOSAuth.mockReturnValue({
      getAccessToken: mockGetAccessToken,
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      try {
        await result.current.getToken();
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
        expect((error as Error).message).toBe('Network error');
      }
    });
  });
});
