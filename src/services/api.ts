// API Service for Websets Backend
// Allow overriding the backend URL via environment variables
const API_BASE =
  (typeof process !== 'undefined' && process.env.VITE_API_BASE) ||
  'http://localhost:8001';
const API_VERSION = 'v1'; // Default to v1
const VERSIONED_API_BASE = `${API_BASE}/${API_VERSION}`;

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
}

export interface Job {
  id: string;
  prompt: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  created_at: string;
  updated_at: string;
  user_id: string;
  progress?: number;
  error_message?: string;
}

export interface Dataset {
  id: string;
  name: string;
  description: string;
  record_count: number;
  created_at: string;
  job_id: string;
}

export interface DatasetRecord {
  id: string;
  content: any;
  metadata: any;
  created_at: string;
}

export interface ApiError extends Error {
  status: number;
  statusText: string;
  data?: any;
  retryAfter?: string;
}

export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface ErrorResponse {
  detail?: string | ValidationError[];
  error?: string;
  message?: string;
}

class ApiService {
  private token: string | (() => Promise<string | null>) | null = null;
  private refreshToken: string | null = null;
  private readonly maxRetries = 3;
  private readonly retryDelay = 1000; // 1 second
  private useVersionedEndpoints = true; // Toggle for versioned vs legacy endpoints
  private baseUrl: string;

  constructor() {
    // Tokens are kept only in memory when using cookie-based sessions
    this.token = null;
    this.refreshToken = null;
    this.baseUrl = this.useVersionedEndpoints ? VERSIONED_API_BASE : API_BASE;
  }

  private getBaseUrl(endpoint: string): string {
    return this.useVersionedEndpoints ? `${VERSIONED_API_BASE}${endpoint}` : `${API_BASE}${endpoint}`;
  }

  setApiVersion(version: string) {
    this.useVersionedEndpoints = true;
    // Could be extended to support different versions
  }

  setLegacyMode(useLegacy: boolean) {
    this.useVersionedEndpoints = !useLegacy;
  }

  setTokenProvider(fn: () => Promise<string | null>) {
    this.token = fn;
  }

  private async delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private shouldRetry(error: ApiError, attemptNumber: number): boolean {
    if (attemptNumber >= this.maxRetries) return false;
    
    // Retry on network errors or server errors (5xx)
    return (
      !error.status || // Network error
      error.status >= 500 || // Server error
      error.status === 429 // Rate limit (with exponential backoff)
    );
  }

  private async getHeaders(includeAuth = true) {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (includeAuth && this.token) {
      let token: string | null = null;
      if (typeof this.token === 'function') {
        try {
          token = await this.token();
        } catch {
          token = null;
        }
      } else {
        token = this.token;
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    return headers;
  }

  private async handleResponse(response: Response) {
    if (!response.ok) {
      let errorData: any;
      let errorMessage = `API Error: ${response.status}`;
      
      try {
        // Try to parse as JSON first
        const contentType = response.headers.get('Content-Type');
        if (contentType?.includes('application/json')) {
          errorData = await response.json();
          
          // Handle different error response formats
          if (errorData.detail) {
            // FastAPI style error
            if (Array.isArray(errorData.detail)) {
              // Validation errors
              errorMessage = errorData.detail.map((err: any) => err.msg).join(', ');
            } else {
              errorMessage = errorData.detail;
            }
          } else if (errorData.error) {
            // Custom error format
            errorMessage = errorData.error;
          } else if (errorData.message) {
            // Generic message format
            errorMessage = errorData.message;
          }
        } else {
          // Fallback to text
          errorData = await response.text();
          errorMessage = errorData || `HTTP ${response.status}`;
        }
      } catch (parseError) {
        // If parsing fails, use status text
        errorMessage = response.statusText || `HTTP ${response.status}`;
      }

      // Create structured error object
      const apiError = new Error(errorMessage) as any;
      apiError.status = response.status;
      apiError.statusText = response.statusText;
      apiError.data = errorData;
      
      // Handle specific status codes
      if (response.status === 401) {
        // Clear token on unauthorized
        this.logout();
        apiError.message = 'Session expired. Please log in again.';
      } else if (response.status === 403) {
        apiError.message = 'Access forbidden. You do not have permission for this action.';
      } else if (response.status === 429) {
        // Rate limit exceeded
        const retryAfter = response.headers.get('Retry-After');
        apiError.message = `Rate limit exceeded. ${retryAfter ? `Try again in ${retryAfter} seconds.` : 'Please wait before trying again.'}`;
        apiError.retryAfter = retryAfter;
      } else if (response.status >= 500) {
        apiError.message = 'Server error. Please try again later.';
      }
      
      throw apiError;
    }
    
    try {
      return await response.json();
    } catch (error) {
      // Handle non-JSON responses
      return await response.text();
    }
  }

  private async fetchWithRetry(
    url: string,
    options: RequestInit = {},
    attemptNumber = 1
  ): Promise<Response> {
    try {
      const response = await fetch(url, options);
      return response;
    } catch (error) {
      const apiError = error as ApiError;
      
      if (this.shouldRetry(apiError, attemptNumber)) {
        const delayMs = this.retryDelay * Math.pow(2, attemptNumber - 1); // Exponential backoff
        await this.delay(delayMs);
        return this.fetchWithRetry(url, options, attemptNumber + 1);
      }
      
      throw error;
    }
  }

  private async refreshAccessToken() {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }
    const response = await fetch(this.getBaseUrl('/auth/refresh'), {
      method: 'POST',
      headers: await this.getHeaders(false),
      body: JSON.stringify({ refresh_token: this.refreshToken }),
    });
    const data = await this.handleResponse(response);
    this.token = data.access_token;
    this.refreshToken = data.refresh_token;
  }

  private async request(
    endpoint: string,
    options: RequestInit = {},
    includeAuth = true
  ): Promise<Response> {
    const url = this.getBaseUrl(endpoint);
    const headers = await this.getHeaders(includeAuth);

    const requestOptions: RequestInit = {
      ...options,
      headers: {
        ...headers,
        ...(options.headers || {}),
      },
      // Always include credentials for cookie-based auth (WorkOS)
      credentials: 'include',
    };

    try {
      const response = await this.fetchWithRetry(url, requestOptions);
      
      // Handle token refresh if needed
      if (response.status === 401 && this.refreshToken) {
        try {
          await this.refreshAccessToken();
          return await this.fetchWithRetry(url, requestOptions);
        } catch (refreshError) {
          this.logout();
          throw refreshError;
        }
      }
      
      return response;
    } catch (error) {
      throw error;
    }
  }

  // Authentication
  async register(email: string, password: string, fullName: string): Promise<User> {
    const response = await this.request(
      '/auth/register',
      {
        method: 'POST',
        body: JSON.stringify({
          email,
          password,
          full_name: fullName,
        }),
      },
      false
    );

    return this.handleResponse(response);
  }

  async login(
    email: string,
    password: string
  ): Promise<{ access_token: string; token_type: string; refresh_token: string }> {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    try {
      const response = await this.fetchWithRetry(this.getBaseUrl('/auth/login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      });

      const data = await this.handleResponse(response);
      this.token = data.access_token;
      this.refreshToken = data.refresh_token;
      return data;
    } catch (error: any) {
      // Provide clearer message for network failures
      if (error instanceof TypeError && error.message === 'Failed to fetch') {
        error.message = 'Unable to reach the server. Is the backend running?';
      }
      throw error;
    }
  }

  async passwordResetRequest(email: string): Promise<{ message: string; token: string }> {
    const response = await this.request(
      '/auth/password-reset/request',
      {
        method: 'POST',
        body: JSON.stringify({ email }),
      },
      false
    );
    return this.handleResponse(response);
  }

  async passwordResetConfirm(token: string, newPassword: string): Promise<{ message: string }> {
    const response = await this.request(
      '/auth/password-reset/confirm',
      {
        method: 'POST',
        body: JSON.stringify({ token, new_password: newPassword }),
      },
      false
    );
    return this.handleResponse(response);
  }

  async getCurrentUser(): Promise<User> {
    console.log('Getting current user');
    
    try {
      // For WorkOS with HTTP-only cookies, we need to make a request to the backend
      // The backend will validate the session cookie and return the user info
      console.log('Fetching from:', `${API_BASE}/api/auth/me`);
      
      const response = await fetch(`${API_BASE}/api/auth/me`, {
        method: 'GET',
        credentials: 'include', // Critical: Include cookies in the request
        headers: {
          'Accept': 'application/json'
        }
      });
      
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        // If we get a 401, the session is invalid or expired
        if (response.status === 401) {
          console.log('Session invalid or expired, redirecting to login');
          // Clear any local tokens
          this.token = null;
          // Return to login page
          window.location.href = '/';
          throw new Error('Session expired');
        }
        
        console.error('Failed to get user:', response.status, response.statusText);
        throw new Error(`Failed to get user: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('User data received:', data);
      
      // If we successfully get user data, we're authenticated
      // Set a flag in localStorage to remember authentication state
      localStorage.setItem('websets_authenticated', 'true');
      
      return data;
    } catch (error) {
      console.error('Error getting current user:', error);
      throw error;
    }
  }

  async logout(): Promise<void> {
    // Clear any local authentication flags
    this.token = null;
    localStorage.removeItem('websets_authenticated');
    
    // Redirect to backend logout endpoint which will clear the session cookie
    // and redirect to WorkOS logout URL
    window.location.href = `${API_BASE}/api/auth/logout`;
  }

  // Jobs
  async getJobs(): Promise<Job[]> {
    const response = await this.request('/jobs/');
    
    return this.handleResponse(response);
  }

  async getJob(jobId: string): Promise<Job> {
    const response = await this.request('/jobs/' + jobId);
    
    return this.handleResponse(response);
  }

  async createJob(prompt: string, options?: { estimated_urls?: number; complexity?: string }): Promise<Job> {
    const response = await this.request(
      '/jobs/',
      {
        method: 'POST',
        body: JSON.stringify({
          prompt,
          ...options,
        }),
      }
    );
    
    return this.handleResponse(response);
  }

  async cancelJob(jobId: string): Promise<void> {
    const response = await this.request('/jobs/' + jobId, { method: 'DELETE' });
    
    if (!response.ok) {
      throw new Error(`Failed to cancel job: ${response.status}`);
    }
  }

  // Datasets
  async getDatasets(): Promise<Dataset[]> {
    const response = await this.request('/datasets/');
    
    return this.handleResponse(response);
  }

  async getDataset(datasetId: string): Promise<Dataset> {
    const response = await this.request('/datasets/' + datasetId);
    
    return this.handleResponse(response);
  }

  async getDatasetRecords(datasetId: string, limit = 50, offset = 0): Promise<DatasetRecord[]> {
    const response = await this.request(
      `/datasets/${datasetId}/records?limit=${limit}&offset=${offset}`
    );
    
    return this.handleResponse(response);
  }

  async searchDataset(datasetId: string, query: string, limit = 10, threshold = 0.7): Promise<DatasetRecord[]> {
    const response = await this.request(`/datasets/${datasetId}/search`, {
      method: 'POST',
      body: JSON.stringify({
        query,
        limit,
        threshold,
      }),
    });
    
    return this.handleResponse(response);
  }

  async exportDataset(datasetId: string, format: 'json' | 'csv' = 'json'): Promise<Blob> {
    const response = await this.request(
      `/datasets/${datasetId}/export?format=${format}`
    );
    
    if (!response.ok) {
      throw new Error(`Failed to export dataset: ${response.status}`);
    }
    
    return response.blob();
  }

  // Health
  async getHealth(): Promise<{ status: string; timestamp: string }> {
    const response = await this.request('/health/', {}, false);
    return this.handleResponse(response);
  }

  async getDetailedHealth(): Promise<any> {
    const response = await this.request('/health/detailed', {}, false);
    return this.handleResponse(response);
  }

  async processWorkOSCallback(code: string): Promise<void> {
    const response = await fetch(
      `${API_BASE}/api/auth/callback?code=${encodeURIComponent(code)}`,
      {
        method: 'GET',
        credentials: 'include',
      }
    );

    if (!response.ok) {
      throw new Error(`Auth callback failed: ${response.status}`);
    }
  }

  // Utility methods
  isAuthenticated(): boolean {
    // Check token in memory
    const hasToken = !!this.token;

    // Local storage flag set after successful auth
    const hasAuthFlag = localStorage.getItem('websets_authenticated') === 'true';

    console.log('Authentication check:', {
      hasToken,
      hasAuthFlag,
      result: hasToken || hasAuthFlag,
    });

    return hasToken || hasAuthFlag;
  }

  getToken(): string | null {
    return typeof this.token === 'string' ? this.token : null;
  }
}

export const apiService = new ApiService();
export default apiService;
