import apiService from './api';

const BASE_URL = 'http://localhost:8000/v1';

describe('apiService', () => {
  beforeEach(() => {
    apiService.logout();
  });

  test('login success sets tokens', async () => {
    const tokenData = { access_token: 'abc', token_type: 'bearer', refresh_token: 'def' };
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(tokenData),
    } as any);

    const result = await apiService.login('test@example.com', 'password');

    expect(fetch).toHaveBeenCalledWith(
      `${BASE_URL}/auth/login`,
      expect.objectContaining({ method: 'POST' })
    );
    expect(result).toEqual(tokenData);
    expect(apiService.isAuthenticated()).toBe(true);
    expect(apiService.getToken()).toBe('abc');
  });

  test('login network error returns friendly message', async () => {
    (fetch as jest.Mock).mockRejectedValue(new TypeError('Failed to fetch'));
    await expect(apiService.login('a','b')).rejects.toThrow('Unable to reach the server. Is the backend running?');
  });

  test('logout clears tokens', async () => {
    const tokenData = { access_token: 'abc', token_type: 'bearer', refresh_token: 'def' };
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(tokenData),
    } as any);
    await apiService.login('e','p');

    apiService.logout();

    expect(apiService.isAuthenticated()).toBe(false);
    expect(apiService.getToken()).toBe(null);
  });

  test('register sends request and returns data', async () => {
    const userData = { id: '1', email: 'e', full_name: 'Test', is_active: true };
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(userData),
    } as any);

    const result = await apiService.register('e','p','Test');

    expect(fetch).toHaveBeenCalledWith(
      `${BASE_URL}/auth/register`,
      expect.objectContaining({ method: 'POST' })
    );
    expect(result).toEqual(userData);
  });

  test('handles unauthorized responses by logging out', async () => {
    const tokenData = { access_token: 'abc', token_type: 'bearer', refresh_token: 'def' };
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(tokenData),
    } as any);
    await apiService.login('e','p');

    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      headers: { get: jest.fn() },
      json: jest.fn().mockResolvedValue({ detail: 'Unauthorized' }),
    } as any);
    (fetch as jest.Mock).mockRejectedValueOnce(new Error('refresh failed'));

    await expect(apiService.getHealth()).rejects.toThrow('refresh failed');
    expect(apiService.isAuthenticated()).toBe(false);
  });
});
