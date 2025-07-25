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
  global.fetch = jest.fn();
});

describe('apiService getHeaders', () => {
  test('returns base headers', async () => {
    const headers = await anyService.getHeaders();
    expect(headers['Content-Type']).toBe('application/json');
  });
});

describe('apiService login', () => {
  test('stores tokens on success', async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      mockResponse({ access_token: 'a', refresh_token: 'r', token_type: 'Bearer' })
    );
    await apiService.login('u@example.com', 'pw');
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/auth/login'),
      expect.objectContaining({ method: 'POST' })
    );
  });

  test('provides helpful message on network failure', async () => {
    (global.fetch as jest.Mock).mockRejectedValue(new TypeError('Failed to fetch'));
    await expect(apiService.login('u@example.com', 'pw')).rejects.toThrow(
      'Unable to reach the server. Is the backend running?'
    );
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
