import { useEffect, ReactNode } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import apiService from '@/services/api';
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
  const { isAuthenticated, isLoading, user, getAccessTokenSilently, logout } = useAuth0();
  const { setUser, setAuthenticated, setLoading, reset } = useGlobalStore();

  useEffect(() => {
    setUser(user);
    setAuthenticated(isAuthenticated);
    setLoading(isLoading);
  }, [user, isAuthenticated, isLoading, setUser, setAuthenticated, setLoading]);

  apiService.setTokenProvider(async () => {
    try {
      return await getAccessTokenSilently();
    } catch {
      return null;
    }
  });

  useEffect(() => {
    return () => {
      logout({ logoutParams: { returnTo: window.location.origin } });
      reset();
    };
  }, [logout, reset]);

  return <>{children}</>;
};

export { AuthProvider };
export default AuthProvider;
