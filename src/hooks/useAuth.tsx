import { createContext, useContext, useEffect, ReactNode } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import apiService from '@/services/api';
import { useAuthStore } from '@/store/auth';

interface AuthContextType {
  user: any;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: () => void;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
};

export const useAuthProvider = () => {
  const {
    user,
    isLoading,
    isAuthenticated,
    error,
    setUser,
    setLoading,
    setAuthenticated,
    setError,
    reset,
  } = useAuthStore();

  useEffect(() => {
    const check = async () => {
      if ((apiService as any).isAuthenticated?.()) {
        try {
          const current = await apiService.getCurrentUser();
          setUser(current);
          setAuthenticated(true);
        } catch (err: any) {
          setError(err.message);
          apiService.logout();
          reset();
        }
      }
      setLoading(false);
    };
    check();
  }, []);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      await apiService.login(email, password);
      const current = await apiService.getCurrentUser();
      setUser(current);
      setAuthenticated(true);
      setError(null);
    } catch (err: any) {
      setUser(null);
      setAuthenticated(false);
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, password: string, fullName: string) => {
    setLoading(true);
    try {
      await apiService.register(email, password, fullName);
      await login(email, password);
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
      throw err;
    }
  };

  const requestPasswordReset = async (email: string) => {
    setLoading(true);
    try {
      await apiService.passwordResetRequest(email);
      setError(null);
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const confirmPasswordReset = async (token: string, newPassword: string) => {
    setLoading(true);
    try {
      await apiService.passwordResetConfirm(token, newPassword);
      setError(null);
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    apiService.logout();
    reset();
  };

  return {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    requestPasswordReset,
    confirmPasswordReset,
    error,
  };
};

const AuthProvider = ({ children }: { children: ReactNode }) => {
  const { isAuthenticated, isLoading, user, loginWithRedirect, logout, getAccessTokenSilently } = useAuth0();
  const {
    setUser,
    setAuthenticated,
    setLoading,
    reset,
    user: storeUser,
    isLoading: storeLoading,
    isAuthenticated: storeAuthenticated,
  } = useAuthStore();

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

  const value: AuthContextType = {
    user: storeUser,
    isLoading: storeLoading,
    isAuthenticated: storeAuthenticated,
    login: () => loginWithRedirect(),
    logout: () => {
      logout({ logoutParams: { returnTo: window.location.origin } });
      reset();
    },
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export { AuthProvider };
export default AuthProvider;
