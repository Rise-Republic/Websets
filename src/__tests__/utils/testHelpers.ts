/**
 * Test Utilities and Helpers
 * Common utilities for testing across the application
 */

import { render, RenderOptions } from '@testing-library/react';
import { ReactElement } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock data generators
export const mockDataset = (overrides = {}) => ({
  id: 1,
  name: 'Test Dataset',
  description: 'A test dataset for unit testing',
  status: 'active',
  created_at: '2024-01-01T12:00:00Z',
  updated_at: '2024-01-01T12:00:00Z',
  record_count: 1000,
  tags: ['test'],
  source_urls: ['https://example.com'],
  ...overrides,
});

export const mockSearchResult = (overrides = {}) => ({
  id: 1,
  title: 'Test Result',
  content: 'Test content for search result',
  url: 'https://example.com/test',
  score: 0.95,
  dataset_id: 1,
  metadata: {
    extracted_at: '2024-01-01T12:00:00Z',
    content_type: 'article',
  },
  ...overrides,
});

export const mockAnalytics = (overrides = {}) => ({
  metrics: {
    total_datasets: 10,
    active_datasets: 8,
    total_records: 50000,
    crawl_success_rate: 0.95,
    avg_processing_time_minutes: 12.5,
  },
  trends: {
    datasets_created_last_30_days: 3,
    records_processed_last_24_hours: 2500,
  },
  top_domains: [
    { domain: 'example.com', record_count: 5000, success_rate: 0.98 },
    { domain: 'test-site.com', record_count: 3000, success_rate: 0.96 },
  ],
  ...overrides,
});

// Test providers wrapper
interface AllTheProvidersProps {
  children: React.ReactNode;
}

const AllTheProviders = ({ children }: AllTheProvidersProps) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

// Custom render function
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };

// Common test utilities
export const waitForLoadingToFinish = () => {
  return new Promise(resolve => setTimeout(resolve, 0));
};

export const createMockApiResponse = <T>(data: T, delay = 0) => {
  return new Promise<T>(resolve => {
    setTimeout(() => resolve(data), delay);
  });
};

// Error boundary for testing error states
export class TestErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return <div>Something went wrong.</div>;
    }

    return this.props.children;
  }
}

// Mock implementations for common hooks
export const mockUseAuth = {
  user: {
    id: 'test-user-id',
    email: 'test@example.com',
    name: 'Test User',
  },
  isAuthenticated: true,
  isLoading: false,
  login: jest.fn(),
  logout: jest.fn(),
  getToken: jest.fn().mockResolvedValue('mock-token'),
};

export const mockUseDatasets = {
  datasets: [mockDataset()],
  isLoading: false,
  error: null,
  refetch: jest.fn(),
  createDataset: jest.fn(),
  updateDataset: jest.fn(),
  deleteDataset: jest.fn(),
};

export const mockUseSearch = {
  results: [mockSearchResult()],
  isLoading: false,
  error: null,
  search: jest.fn(),
  clearResults: jest.fn(),
};

// Test data constants
export const TEST_CONSTANTS = {
  API_BASE_URL: 'http://localhost:8000',
  DEFAULT_TIMEOUT: 5000,
  MOCK_USER_ID: 'test-user-123',
  MOCK_TENANT_ID: 'test-tenant-456',
} as const;

// Assertion helpers
export const expectElementToBeVisible = (element: HTMLElement) => {
  expect(element).toBeInTheDocument();
  expect(element).toBeVisible();
};

export const expectElementToHaveAccessibleName = (
  element: HTMLElement,
  name: string
) => {
  expect(element).toHaveAccessibleName(name);
};

export const expectFormToBeValid = (form: HTMLFormElement) => {
  expect(form).toBeValid();
  expect(form.checkValidity()).toBe(true);
};

// Mock fetch implementation
export const createMockFetch = (responses: Record<string, any>) => {
  return jest.fn().mockImplementation((url: string) => {
    const response = responses[url];
    if (!response) {
      return Promise.reject(new Error(`No mock response for ${url}`));
    }

    return Promise.resolve({
      ok: response.status >= 200 && response.status < 300,
      status: response.status || 200,
      json: () => Promise.resolve(response.data),
      text: () => Promise.resolve(JSON.stringify(response.data)),
    });
  });
};

// Performance testing helpers
export const measureRenderTime = async (renderFn: () => void) => {
  const start = performance.now();
  renderFn();
  await waitForLoadingToFinish();
  const end = performance.now();
  return end - start;
};

// Accessibility testing helpers
export const getByRoleWithTimeout = async (
  container: HTMLElement,
  role: string,
  options?: any,
  timeout = 1000
) => {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new Error(`Element with role "${role}" not found within ${timeout}ms`));
    }, timeout);

    const checkForElement = () => {
      try {
        const element = container.querySelector(`[role="${role}"]`);
        if (element) {
          clearTimeout(timer);
          resolve(element);
        } else {
          setTimeout(checkForElement, 50);
        }
      } catch (error) {
        clearTimeout(timer);
        reject(error);
      }
    };

    checkForElement();
  });
};
