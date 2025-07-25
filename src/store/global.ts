import { create } from 'zustand';
import apiService from '@/services/api';

export interface GlobalState {
  user: any;
  tenantId: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  features: Record<string, boolean>;
}

export interface GlobalActions {
  setUser: (user: any) => void;
  setTenantId: (tenantId: string | null) => void;
  setAuthenticated: (auth: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setFeatureFlag: (flag: string, enabled: boolean) => void;
  checkAuth: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  requestPasswordReset: (email: string) => Promise<void>;
  confirmPasswordReset: (token: string, newPassword: string) => Promise<void>;
  logout: () => void;
  reset: () => void;
}

const initialState: Omit<GlobalState, never> = {
  user: null,
  tenantId: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
  features: {},
};

export const useGlobalStore = create<GlobalState & GlobalActions>((set, get) => ({
  ...initialState,
  setUser: (user) => set({ user }),
  setTenantId: (tenantId) => set({ tenantId }),
  setAuthenticated: (auth) => set({ isAuthenticated: auth }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  setFeatureFlag: (flag, enabled) =>
    set((state) => ({ features: { ...state.features, [flag]: enabled } })),
  reset: () => set({ ...initialState, isLoading: false }),
  checkAuth: async () => {
    console.log('Starting checkAuth...');
    set({ isLoading: true });
    try {
      const current = await apiService.getCurrentUser();
      console.log('User data received:', current);
      set({
        user: current,
        tenantId: (current as any).tenant_id ?? null,
        isAuthenticated: true,
        error: null,
      });
      apiService.setTenantId((current as any).tenant_id ?? null);
      console.log('Authentication state updated: true');
    } catch (err: any) {
      console.error('Error fetching user:', err);
      set({
        isAuthenticated: false,
        tenantId: null,
        user: null,
        error: err.message,
      });
      apiService.setTenantId(null);
    } finally {
      set({ isLoading: false });
      console.log('checkAuth complete, state:', {
        isAuthenticated: get().isAuthenticated,
        user: get().user,
        error: get().error,
      });
    }
  },
  login: async (email, password) => {
    set({ isLoading: true });
    try {
      await apiService.login(email, password);
      const current = await apiService.getCurrentUser();
      set({
        user: current,
        tenantId: (current as any).tenant_id ?? null,
        isAuthenticated: true,
        error: null,
      });
      apiService.setTenantId((current as any).tenant_id ?? null);
    } catch (err: any) {
      set({ user: null, isAuthenticated: false, error: err.message });
      throw err;
    } finally {
      set({ isLoading: false });
    }
  },
  register: async (email, password, fullName) => {
    set({ isLoading: true });
    try {
      await apiService.register(email, password, fullName);
      await get().login(email, password);
    } catch (err: any) {
      set({ error: err.message });
      set({ isLoading: false });
      throw err;
    }
  },
  requestPasswordReset: async (email) => {
    set({ isLoading: true });
    try {
      await apiService.passwordResetRequest(email);
      set({ error: null });
    } catch (err: any) {
      set({ error: err.message });
      throw err;
    } finally {
      set({ isLoading: false });
    }
  },
  confirmPasswordReset: async (token, newPassword) => {
    set({ isLoading: true });
    try {
      await apiService.passwordResetConfirm(token, newPassword);
      set({ error: null });
    } catch (err: any) {
      set({ error: err.message });
      throw err;
    } finally {
      set({ isLoading: false });
    }
  },
  logout: () => {
    apiService.logout();
    get().reset();
  },
}));

