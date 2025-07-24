import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import apiService from '@/services/api';

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
  const [user, setUser] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const check = async () => {
      if ((apiService as any).isAuthenticated?.()) {
        try {
          const current = await apiService.getCurrentUser();
          setUser(current);
          setIsAuthenticated(true);
        } catch (err: any) {
          setError(err.message);
          apiService.logout();
        }
      }
      setIsLoading(false);
    };
    check();
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      await apiService.login(email, password);
      const current = await apiService.getCurrentUser();
      setUser(current);
      setIsAuthenticated(true);
      setError(null);
    } catch (err: any) {
      setUser(null);
      setIsAuthenticated(false);
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string, fullName: string) => {
    setIsLoading(true);
    try {
      await apiService.register(email, password, fullName);
      await login(email, password);
    } catch (err: any) {
      setError(err.message);
      setIsLoading(false);
      throw err;
    }
  };

  const logout = () => {
    apiService.logout();
    setUser(null);
    setIsAuthenticated(false);
    setError(null);
  };

  return { user, isLoading, isAuthenticated, login, register, logout, error };
};

const AuthProvider = ({ children }: { children: ReactNode }) => {
  const { isAuthenticated, isLoading, user, loginWithRedirect, logout, getAccessTokenSilently } = useAuth0();

  apiService.setTokenProvider(async () => {
    try {
      return await getAccessTokenSilently();
    } catch {
      return null;
    }
  });

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login: () => loginWithRedirect(),
    logout: () => logout({ logoutParams: { returnTo: window.location.origin } }),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export { AuthProvider };
export default AuthProvider;
