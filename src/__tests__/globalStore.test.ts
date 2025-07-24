import { act } from '@testing-library/react';
import { useGlobalStore } from '@/store/global';
import * as apiService from '@/services/api';

jest.mock('@/services/api');
const mockApi = apiService as jest.Mocked<typeof apiService>;

const mockDefaultApi = {
  login: jest.fn(),
  register: jest.fn(),
  logout: jest.fn(),
  getCurrentUser: jest.fn(),
  isAuthenticated: jest.fn(),
  passwordResetRequest: jest.fn(),
  passwordResetConfirm: jest.fn(),
};
(apiService as any).default = mockDefaultApi;

beforeEach(() => {
  jest.clearAllMocks();
  mockDefaultApi.isAuthenticated.mockReturnValue(false);
  useGlobalStore.getState().reset();
});

test('setters update state', () => {
  const { setUser, setTenantId, setFeatureFlag } = useGlobalStore.getState();
  act(() => {
    setUser({ name: 'x' });
    setTenantId('t1');
    setFeatureFlag('demo', true);
  });
  const state = useGlobalStore.getState();
  expect(state.user).toEqual({ name: 'x' });
  expect(state.tenantId).toBe('t1');
  expect(state.features.demo).toBe(true);
});

test('login stores user on success', async () => {
  const user = { id: 'u1' };
  mockDefaultApi.login.mockResolvedValue(undefined);
  mockDefaultApi.getCurrentUser.mockResolvedValue(user);
  await act(async () => {
    await useGlobalStore.getState().login('e', 'p');
  });
  const state = useGlobalStore.getState();
  expect(state.user).toEqual(user);
  expect(state.isAuthenticated).toBe(true);
  expect(state.error).toBe(null);
});

test('logout resets state', () => {
  const { logout, setUser } = useGlobalStore.getState();
  act(() => {
    setUser({ id: '1' });
  });
  logout();
  const state = useGlobalStore.getState();
  expect(state.user).toBe(null);
  expect(state.isAuthenticated).toBe(false);
});
