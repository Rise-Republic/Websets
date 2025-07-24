import { create } from 'zustand';

export interface AuthState {
  user: any;
  tenantId: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface AuthActions {
  setUser: (user: any) => void;
  setTenantId: (tenantId: string | null) => void;
  setAuthenticated: (auth: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useAuthStore = create<AuthState & AuthActions>((set) => ({
  user: null,
  tenantId: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
  setUser: (user) => set({ user }),
  setTenantId: (tenantId) => set({ tenantId }),
  setAuthenticated: (auth) => set({ isAuthenticated: auth }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  reset: () =>
    set({ user: null, tenantId: null, isAuthenticated: false, isLoading: false, error: null }),
}));
