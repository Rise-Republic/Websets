import apiService from './api';

// Helpers to access private methods/fields
const anyService = apiService as any;

function mockResponse(data: any, status = 200, headers = { 'Content-Type': 'application/json' }) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: 'OK',
    headers: { get: (name: string) => headers[name] },
    json: async () => data,
    text: async () => JSON.stringify(data),
  } as any;
}

beforeEach(() => {
  jest.clearAllMocks();
  apiService.logout();
  global.fetch = jest.fn();
  global.localStorage = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
  } as any;
});

describe('apiService getHeaders', () => {
  test('returns Authorization header when token is string', async () => {
    anyService.token = 'abc';
    const headers = await anyService.getHeaders();
    expect(headers['Authorization']).toBe('Bearer abc');
  });

  test('calls token provider function', async () => {
    const provider = jest.fn().mockResolvedValue('def');
    apiService.setTokenProvider(provider);
    const headers = await anyService.getHeaders();
    expect(provider).toHaveBeenCalled();
    expect(headers['Authorization']).toBe('Bearer def');
  });

  test('omits Authorization if provider throws', async () => {
    apiService.setTokenProvider(() => Promise.reject(new Error('bad')));
    const headers = await anyService.getHeaders();
    expect(headers['Authorization']).toBeUndefined();
  });

  test('includes tenant header when tenantId set', async () => {
    anyService.tenantId = 'org1';
    const headers = await anyService.getHeaders();
    expect(headers['X-Org-ID']).toBe('org1');
  });

  test('omits tenant header when tenantId null', async () => {
    anyService.tenantId = null;
    const headers = await anyService.getHeaders();
    expect(headers['X-Org-ID']).toBeUndefined();
  });
});

describe('apiService login', () => {
  test('returns tokens on success', async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      mockResponse({ access_token: 'a', refresh_token: 'r', token_type: 'Bearer' })
    );
    await apiService.login('u@example.com', 'pw');
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/auth/login'),
      expect.objectContaining({ method: 'POST' })
    );
    expect(apiService.getToken()).toBe('a');
    expect(apiService.isAuthenticated()).toBe(true);
    expect(global.localStorage.setItem).not.toHaveBeenCalled();
  });

  test('provides helpful message on network failure', async () => {
    (global.fetch as jest.Mock).mockRejectedValue(new TypeError('Failed to fetch'));
    await expect(apiService.login('u@example.com', 'pw')).rejects.toThrow(
      'Unable to reach the server. Is the backend running?'
    );
  });
});

describe('authentication helpers', () => {
  test('isAuthenticated and getToken reflect logout', () => {
    anyService.token = 'zz';
    expect(apiService.isAuthenticated()).toBe(true);
    apiService.logout();
    expect(apiService.isAuthenticated()).toBe(false);
    expect(apiService.getToken()).toBeNull();
  });
});

describe('apiService internals', () => {
  test('getBaseUrl switches with legacy mode', () => {
    anyService.setLegacyMode(false);
    expect(anyService.getBaseUrl('/x')).toMatch(/v1\/x$/);
    anyService.setLegacyMode(true);
    expect(anyService.getBaseUrl('/x')).toMatch(/\/x$/);
  });

  test('shouldRetry logic', () => {
    expect(anyService.shouldRetry({ status: 0 }, 1)).toBe(true);
    expect(anyService.shouldRetry({ status: 503 }, 2)).toBe(true);
    expect(anyService.shouldRetry({ status: 400 }, 1)).toBe(false);
    expect(anyService.shouldRetry({ status: 503 }, 3)).toBe(false);
  });
});
