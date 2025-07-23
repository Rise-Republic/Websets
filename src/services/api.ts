// API Service for Websets Backend
// Allow overriding the backend URL via Vite environment variables
const API_BASE =
  (typeof import.meta !== 'undefined' && (import.meta as any).env && (import.meta as any).env.VITE_API_BASE) ||
  'http://localhost:8000';
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
  private token: string | null = null;
  private readonly maxRetries = 3;
  private readonly retryDelay = 1000; // 1 second
  private useVersionedEndpoints = true; // Toggle for versioned vs legacy endpoints

  constructor() {
    // Load token from localStorage if available
    this.token = localStorage.getItem('websets_token');
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

  private getHeaders(includeAuth = true) {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (includeAuth && this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
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

  // Authentication
  async register(email: string, password: string, fullName: string): Promise<User> {
    const response = await fetch(this.getBaseUrl('/auth/register'), {
      method: 'POST',
      headers: this.getHeaders(false),
      body: JSON.stringify({
        email,
        password,
        full_name: fullName,
      }),
    });
    
    return this.handleResponse(response);
  }

  async login(
    email: string,
    password: string
  ): Promise<{ access_token: string; token_type: string }> {
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
      localStorage.setItem('websets_token', this.token!);
      return data;
    } catch (error: any) {
      // Provide clearer message for network failures
      if (error instanceof TypeError && error.message === 'Failed to fetch') {
        error.message = 'Unable to reach the server. Is the backend running?';
      }
      throw error;
    }
  }

  async getCurrentUser(): Promise<User> {
    const response = await fetch(this.getBaseUrl('/auth/me'), {
      headers: this.getHeaders(),
    });
    
    return this.handleResponse(response);
  }

  logout() {
    this.token = null;
    localStorage.removeItem('websets_token');
  }

  // Jobs
  async getJobs(): Promise<Job[]> {
    const response = await fetch(this.getBaseUrl('/jobs/'), {
      headers: this.getHeaders(),
    });
    
    return this.handleResponse(response);
  }

  async getJob(jobId: string): Promise<Job> {
    const response = await fetch(this.getBaseUrl('/jobs/' + jobId), {
      headers: this.getHeaders(),
    });
    
    return this.handleResponse(response);
  }

  async createJob(prompt: string, options?: { estimated_urls?: number; complexity?: string }): Promise<Job> {
    const response = await fetch(this.getBaseUrl('/jobs/'), {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        prompt,
        ...options,
      }),
    });
    
    return this.handleResponse(response);
  }

  async cancelJob(jobId: string): Promise<void> {
    const response = await fetch(this.getBaseUrl('/jobs/' + jobId), {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to cancel job: ${response.status}`);
    }
  }

  // Datasets
  async getDatasets(): Promise<Dataset[]> {
    const response = await fetch(this.getBaseUrl('/datasets/'), {
      headers: this.getHeaders(),
    });
    
    return this.handleResponse(response);
  }

  async getDataset(datasetId: string): Promise<Dataset> {
    const response = await fetch(this.getBaseUrl('/datasets/' + datasetId), {
      headers: this.getHeaders(),
    });
    
    return this.handleResponse(response);
  }

  async getDatasetRecords(datasetId: string, limit = 50, offset = 0): Promise<DatasetRecord[]> {
    const response = await fetch(this.getBaseUrl(`/datasets/${datasetId}/records?limit=${limit}&offset=${offset}`), {
      headers: this.getHeaders(),
    });
    
    return this.handleResponse(response);
  }

  async searchDataset(datasetId: string, query: string, limit = 10, threshold = 0.7): Promise<DatasetRecord[]> {
    const response = await fetch(this.getBaseUrl('/datasets/' + datasetId + '/search'), {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        query,
        limit,
        threshold,
      }),
    });
    
    return this.handleResponse(response);
  }

  async exportDataset(datasetId: string, format: 'json' | 'csv' = 'json'): Promise<Blob> {
    const response = await fetch(this.getBaseUrl(`/datasets/${datasetId}/export?format=${format}`), {
      headers: this.getHeaders(),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to export dataset: ${response.status}`);
    }
    
    return response.blob();
  }

  // Health
  async getHealth(): Promise<{ status: string; timestamp: string }> {
    const response = await fetch(this.getBaseUrl('/health/'));
    return this.handleResponse(response);
  }

  async getDetailedHealth(): Promise<any> {
    const response = await fetch(this.getBaseUrl('/health/detailed'));
    return this.handleResponse(response);
  }

  // Utility methods
  isAuthenticated(): boolean {
    return !!this.token;
  }

  getToken(): string | null {
    return this.token;
  }
}

export const apiService = new ApiService();
export default apiService;
