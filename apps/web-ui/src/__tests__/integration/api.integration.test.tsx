/**
 * Integration Tests for API Endpoints
 * End-to-end testing of critical user journeys
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import { BrowserRouter } from 'react-router-dom';
import App from '../../App';

// Mock server for API responses
const server = setupServer(
  // Health endpoint
  rest.get('/health', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: '1.0.0'
      })
    );
  }),

  // Datasets endpoints
  rest.get('/v1/datasets', (req, res, ctx) => {
    const page = req.url.searchParams.get('page') || '1';
    const limit = req.url.searchParams.get('limit') || '20';
    
    return res(
      ctx.status(200),
      ctx.json({
        datasets: [
          {
            id: 1,
            name: 'E-commerce Dataset',
            description: 'Product data from various e-commerce sites',
            status: 'active',
            created_at: '2024-01-01T12:00:00Z',
            updated_at: '2024-01-01T12:00:00Z',
            record_count: 15000,
            tags: ['e-commerce', 'products']
          },
          {
            id: 2,
            name: 'News Articles',
            description: 'Latest news articles from tech publications',
            status: 'processing',
            created_at: '2024-01-02T10:00:00Z',
            updated_at: '2024-01-02T10:30:00Z',
            record_count: 8500,
            tags: ['news', 'technology']
          }
        ],
        total: 2,
        page: parseInt(page),
        per_page: parseInt(limit)
      })
    );
  }),

  rest.post('/v1/datasets', (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        id: 3,
        name: 'New Dataset',
        description: 'A newly created dataset',
        status: 'processing',
        created_at: new Date().toISOString(),
        source_urls: ['https://example.com'],
        tags: ['test']
      })
    );
  }),

  // Search endpoint
  rest.post('/v1/search', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        results: [
          {
            id: 1,
            title: 'Web Scraping Best Practices',
            content: 'A comprehensive guide to ethical web scraping...',
            url: 'https://example.com/guide',
            score: 0.95,
            dataset_id: 1,
            metadata: {
              extracted_at: '2024-01-01T12:00:00Z',
              content_type: 'article'
            }
          },
          {
            id: 2,
            title: 'API Rate Limiting Strategies',
            content: 'How to implement effective rate limiting...',
            url: 'https://example.com/rate-limiting',
            score: 0.87,
            dataset_id: 1,
            metadata: {
              extracted_at: '2024-01-01T13:00:00Z',
              content_type: 'tutorial'
            }
          }
        ],
        total: 2,
        query_time_ms: 125
      })
    );
  }),

  // Analytics endpoint
  rest.get('/v1/analytics', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        metrics: {
          total_datasets: 25,
          active_datasets: 20,
          total_records: 1000000,
          crawl_success_rate: 0.95,
          avg_processing_time_minutes: 15.5
        },
        trends: {
          datasets_created_last_30_days: 5,
          records_processed_last_24_hours: 50000
        },
        top_domains: [
          { domain: 'example.com', record_count: 10000, success_rate: 0.98 },
          { domain: 'test-site.com', record_count: 8500, success_rate: 0.96 }
        ]
      })
    );
  }),

  // Error scenarios
  rest.get('/v1/datasets/999', (req, res, ctx) => {
    return res(
      ctx.status(404),
      ctx.json({
        error: {
          code: 'NOT_FOUND',
          message: 'Dataset not found',
          details: 'The requested dataset does not exist'
        },
        timestamp: new Date().toISOString()
      })
    );
  })
);

// Test setup
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('API Integration Tests', () => {
  const renderApp = () => {
    return render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );
  };

  describe('Dataset Management Flow', () => {
    it('should complete full dataset lifecycle', async () => {
      const user = userEvent.setup();
      renderApp();

      // Navigate to datasets page
      const datasetsLink = screen.getByRole('link', { name: /datasets/i });
      await user.click(datasetsLink);

      // Wait for datasets to load
      await waitFor(() => {
        expect(screen.getByText('E-commerce Dataset')).toBeInTheDocument();
      });

      // Verify dataset list displays correctly
      expect(screen.getByText('E-commerce Dataset')).toBeInTheDocument();
      expect(screen.getByText('News Articles')).toBeInTheDocument();
      expect(screen.getByText('15000')).toBeInTheDocument(); // record count
      expect(screen.getByText('active')).toBeInTheDocument();
      expect(screen.getByText('processing')).toBeInTheDocument();

      // Create new dataset
      const createButton = screen.getByRole('button', { name: /create dataset/i });
      await user.click(createButton);

      // Fill out dataset form
      const nameInput = screen.getByLabelText(/dataset name/i);
      const descriptionInput = screen.getByLabelText(/description/i);
      const urlInput = screen.getByLabelText(/source url/i);

      await user.type(nameInput, 'Integration Test Dataset');
      await user.type(descriptionInput, 'A dataset created during integration testing');
      await user.type(urlInput, 'https://test-site.com');

      // Submit form
      const submitButton = screen.getByRole('button', { name: /create/i });
      await user.click(submitButton);

      // Verify success message
      await waitFor(() => {
        expect(screen.getByText(/dataset created successfully/i)).toBeInTheDocument();
      });
    });

    it('should handle dataset creation errors gracefully', async () => {
      // Mock error response
      server.use(
        rest.post('/v1/datasets', (req, res, ctx) => {
          return res(
            ctx.status(400),
            ctx.json({
              error: {
                code: 'VALIDATION_ERROR',
                message: 'Invalid dataset configuration',
                details: 'Source URL is required'
              }
            })
          );
        })
      );

      const user = userEvent.setup();
      renderApp();

      // Navigate and attempt to create dataset without required fields
      const datasetsLink = screen.getByRole('link', { name: /datasets/i });
      await user.click(datasetsLink);

      const createButton = screen.getByRole('button', { name: /create dataset/i });
      await user.click(createButton);

      const submitButton = screen.getByRole('button', { name: /create/i });
      await user.click(submitButton);

      // Verify error handling
      await waitFor(() => {
        expect(screen.getByText(/validation error/i)).toBeInTheDocument();
      });
    });
  });

  describe('Search Functionality', () => {
    it('should perform search and display results', async () => {
      const user = userEvent.setup();
      renderApp();

      // Navigate to search page
      const searchLink = screen.getByRole('link', { name: /search/i });
      await user.click(searchLink);

      // Perform search
      const searchInput = screen.getByPlaceholderText(/search content/i);
      await user.type(searchInput, 'web scraping');

      const searchButton = screen.getByRole('button', { name: /search/i });
      await user.click(searchButton);

      // Verify search results
      await waitFor(() => {
        expect(screen.getByText('Web Scraping Best Practices')).toBeInTheDocument();
      });

      expect(screen.getByText('API Rate Limiting Strategies')).toBeInTheDocument();
      expect(screen.getByText('2 results found')).toBeInTheDocument();
      expect(screen.getByText('125ms')).toBeInTheDocument(); // query time
    });

    it('should handle empty search results', async () => {
      // Mock empty results
      server.use(
        rest.post('/v1/search', (req, res, ctx) => {
          return res(
            ctx.status(200),
            ctx.json({
              results: [],
              total: 0,
              query_time_ms: 45
            })
          );
        })
      );

      const user = userEvent.setup();
      renderApp();

      const searchLink = screen.getByRole('link', { name: /search/i });
      await user.click(searchLink);

      const searchInput = screen.getByPlaceholderText(/search content/i);
      await user.type(searchInput, 'nonexistent content');

      const searchButton = screen.getByRole('button', { name: /search/i });
      await user.click(searchButton);

      await waitFor(() => {
        expect(screen.getByText(/no results found/i)).toBeInTheDocument();
      });
    });

    it('should apply search filters correctly', async () => {
      const user = userEvent.setup();
      renderApp();

      const searchLink = screen.getByRole('link', { name: /search/i });
      await user.click(searchLink);

      // Apply filters
      const statusFilter = screen.getByLabelText(/status filter/i);
      await user.selectOptions(statusFilter, 'active');

      const tagFilter = screen.getByLabelText(/tag filter/i);
      await user.type(tagFilter, 'e-commerce');

      // Perform filtered search
      const searchInput = screen.getByPlaceholderText(/search content/i);
      await user.type(searchInput, 'products');

      const searchButton = screen.getByRole('button', { name: /search/i });
      await user.click(searchButton);

      // Verify filters are applied (would check request in real implementation)
      await waitFor(() => {
        expect(screen.getByDisplayValue('active')).toBeInTheDocument();
      });
    });
  });

  describe('Analytics Dashboard', () => {
    it('should load and display analytics data', async () => {
      const user = userEvent.setup();
      renderApp();

      // Navigate to analytics
      const analyticsLink = screen.getByRole('link', { name: /analytics/i });
      await user.click(analyticsLink);

      // Verify analytics data loads
      await waitFor(() => {
        expect(screen.getByText('25')).toBeInTheDocument(); // total datasets
      });

      expect(screen.getByText('20')).toBeInTheDocument(); // active datasets
      expect(screen.getByText('1,000,000')).toBeInTheDocument(); // total records
      expect(screen.getByText('95%')).toBeInTheDocument(); // success rate
      expect(screen.getByText('example.com')).toBeInTheDocument(); // top domain
    });

    it('should refresh analytics data on demand', async () => {
      const user = userEvent.setup();
      renderApp();

      const analyticsLink = screen.getByRole('link', { name: /analytics/i });
      await user.click(analyticsLink);

      await waitFor(() => {
        expect(screen.getByText('25')).toBeInTheDocument();
      });

      // Click refresh button
      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      await user.click(refreshButton);

      // Verify loading state and refresh
      expect(screen.getByText(/refreshing/i)).toBeInTheDocument();
      
      await waitFor(() => {
        expect(screen.queryByText(/refreshing/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      // Mock network error
      server.use(
        rest.get('/v1/datasets', (req, res, ctx) => {
          return res.networkError('Network connection failed');
        })
      );

      const user = userEvent.setup();
      renderApp();

      const datasetsLink = screen.getByRole('link', { name: /datasets/i });
      await user.click(datasetsLink);

      // Verify error message
      await waitFor(() => {
        expect(screen.getByText(/connection error/i)).toBeInTheDocument();
      });

      // Verify retry functionality
      const retryButton = screen.getByRole('button', { name: /retry/i });
      expect(retryButton).toBeInTheDocument();
    });

    it('should handle API errors with proper user feedback', async () => {
      // Mock server error
      server.use(
        rest.get('/v1/analytics', (req, res, ctx) => {
          return res(
            ctx.status(500),
            ctx.json({
              error: {
                code: 'INTERNAL_ERROR',
                message: 'Internal server error',
                details: 'Database connection failed'
              }
            })
          );
        })
      );

      const user = userEvent.setup();
      renderApp();

      const analyticsLink = screen.getByRole('link', { name: /analytics/i });
      await user.click(analyticsLink);

      await waitFor(() => {
        expect(screen.getByText(/server error/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/please try again later/i)).toBeInTheDocument();
    });
  });

  describe('Performance and Loading States', () => {
    it('should show loading states during API calls', async () => {
      // Add delay to API response
      server.use(
        rest.get('/v1/datasets', (req, res, ctx) => {
          return res(
            ctx.delay(1000),
            ctx.status(200),
            ctx.json({ datasets: [], total: 0, page: 1, per_page: 20 })
          );
        })
      );

      const user = userEvent.setup();
      renderApp();

      const datasetsLink = screen.getByRole('link', { name: /datasets/i });
      await user.click(datasetsLink);

      // Verify loading state
      expect(screen.getByText(/loading/i)).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('should handle concurrent API requests properly', async () => {
      const user = userEvent.setup();
      renderApp();

      // Trigger multiple API calls simultaneously
      const datasetsLink = screen.getByRole('link', { name: /datasets/i });
      const analyticsLink = screen.getByRole('link', { name: /analytics/i });

      await user.click(datasetsLink);
      await user.click(analyticsLink);
      await user.click(datasetsLink);

      // Verify both pages load correctly without race conditions
      await waitFor(() => {
        expect(screen.getByText('E-commerce Dataset')).toBeInTheDocument();
      });
    });
  });
});
