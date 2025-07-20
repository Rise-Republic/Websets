// API Service for Websets Backend
const API_BASE = 'http://localhost:8000';

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

class ApiService {
  private token: string | null = null;

  constructor() {
    // Load token from localStorage if available
    this.token = localStorage.getItem('websets_token');
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
      const error = await response.text();
      throw new Error(`API Error: ${response.status} - ${error}`);
    }
    return response.json();
  }

  // Authentication
  async register(email: string, password: string, fullName: string): Promise<User> {
    const response = await fetch(`${API_BASE}/auth/register`, {
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

  async login(email: string, password: string): Promise<{ access_token: string; token_type: string }> {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });
    
    const data = await this.handleResponse(response);
    this.token = data.access_token;
    localStorage.setItem('websets_token', this.token!);
    
    return data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await fetch(`${API_BASE}/auth/me`, {
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
    const response = await fetch(`${API_BASE}/jobs/`, {
      headers: this.getHeaders(),
    });
    
    return this.handleResponse(response);
  }

  async getJob(jobId: string): Promise<Job> {
    const response = await fetch(`${API_BASE}/jobs/${jobId}`, {
      headers: this.getHeaders(),
    });
    
    return this.handleResponse(response);
  }

  async createJob(prompt: string, options?: { estimated_urls?: number; complexity?: string }): Promise<Job> {
    const response = await fetch(`${API_BASE}/jobs/`, {
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
    const response = await fetch(`${API_BASE}/jobs/${jobId}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to cancel job: ${response.status}`);
    }
  }

  // Datasets
  async getDatasets(): Promise<Dataset[]> {
    const response = await fetch(`${API_BASE}/datasets/`, {
      headers: this.getHeaders(),
    });
    
    return this.handleResponse(response);
  }

  async getDataset(datasetId: string): Promise<Dataset> {
    const response = await fetch(`${API_BASE}/datasets/${datasetId}`, {
      headers: this.getHeaders(),
    });
    
    return this.handleResponse(response);
  }

  async getDatasetRecords(datasetId: string, limit = 50, offset = 0): Promise<DatasetRecord[]> {
    const response = await fetch(`${API_BASE}/datasets/${datasetId}/records?limit=${limit}&offset=${offset}`, {
      headers: this.getHeaders(),
    });
    
    return this.handleResponse(response);
  }

  async searchDataset(datasetId: string, query: string, limit = 10, threshold = 0.7): Promise<DatasetRecord[]> {
    const response = await fetch(`${API_BASE}/datasets/${datasetId}/search`, {
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
    const response = await fetch(`${API_BASE}/datasets/${datasetId}/export?format=${format}`, {
      headers: this.getHeaders(),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to export dataset: ${response.status}`);
    }
    
    return response.blob();
  }

  // Health
  async getHealth(): Promise<{ status: string; timestamp: string }> {
    const response = await fetch(`${API_BASE}/health/`);
    return this.handleResponse(response);
  }

  async getDetailedHealth(): Promise<any> {
    const response = await fetch(`${API_BASE}/health/detailed`);
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
