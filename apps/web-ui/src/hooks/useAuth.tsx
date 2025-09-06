import { useEffect, ReactNode } from 'react';
import { useGlobalStore } from '@/store/global';

export const useAuth = () =>
  useGlobalStore((state) => ({
    user: state.user,
    isLoading: state.isLoading,
    isAuthenticated: state.isAuthenticated,
    login: state.login,
    register: state.register,
    logout: state.logout,
    requestPasswordReset: state.requestPasswordReset,
    confirmPasswordReset: state.confirmPasswordReset,
    error: state.error,
    checkAuth: state.checkAuth, // Expose checkAuth method
  }));

export const useAuthProvider = () => {
  const auth = useAuth();
  const checkAuth = useGlobalStore((s) => s.checkAuth);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return auth;
};

const AuthProvider = ({ children }: { children: ReactNode }) => {
  const checkAuth = useGlobalStore((s) => s.checkAuth);

  useEffect(() => {
    // Check authentication status on app start
    checkAuth();
  }, [checkAuth]);

  return <>{children}</>;
};

export { AuthProvider };
export default AuthProvider;
