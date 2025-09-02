/**
 * Unit Tests for Dashboard Component
 * Testing dashboard functionality and analytics display
 */

import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render, mockAnalytics } from '../utils/testHelpers';
import Dashboard from '../../components/Dashboard/Dashboard';

// Mock the analytics hook
jest.mock('../../hooks/useAnalytics', () => ({
  useAnalytics: jest.fn(),
}));

import { useAnalytics } from '../../hooks/useAnalytics';
const mockUseAnalytics = useAnalytics as jest.MockedFunction<typeof useAnalytics>;

describe('Dashboard Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders dashboard with analytics data', async () => {
    mockUseAnalytics.mockReturnValue({
      data: mockAnalytics(),
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    render(<Dashboard />);

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument(); // total datasets
    expect(screen.getByText('8')).toBeInTheDocument(); // active datasets
    expect(screen.getByText('50,000')).toBeInTheDocument(); // total records
    expect(screen.getByText('95%')).toBeInTheDocument(); // success rate
  });

  it('shows loading state while fetching analytics', () => {
    mockUseAnalytics.mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
      refetch: jest.fn(),
    });

    render(<Dashboard />);

    expect(screen.getByText('Loading analytics...')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('displays error state when analytics fail to load', () => {
    const mockError = new Error('Failed to fetch analytics');
    mockUseAnalytics.mockReturnValue({
      data: null,
      isLoading: false,
      error: mockError,
      refetch: jest.fn(),
    });

    render(<Dashboard />);

    expect(screen.getByText('Error loading analytics')).toBeInTheDocument();
    expect(screen.getByText('Failed to fetch analytics')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('allows refreshing analytics data', async () => {
    const mockRefetch = jest.fn();
    mockUseAnalytics.mockReturnValue({
      data: mockAnalytics(),
      isLoading: false,
      error: null,
      refetch: mockRefetch,
    });

    const user = userEvent.setup();
    render(<Dashboard />);

    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    await user.click(refreshButton);

    expect(mockRefetch).toHaveBeenCalledTimes(1);
  });

  it('displays top domains correctly', () => {
    mockUseAnalytics.mockReturnValue({
      data: mockAnalytics(),
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    render(<Dashboard />);

    expect(screen.getByText('Top Domains')).toBeInTheDocument();
    expect(screen.getByText('example.com')).toBeInTheDocument();
    expect(screen.getByText('test-site.com')).toBeInTheDocument();
    expect(screen.getByText('5,000')).toBeInTheDocument(); // record count
    expect(screen.getByText('98%')).toBeInTheDocument(); // success rate
  });

  it('handles empty analytics data gracefully', () => {
    mockUseAnalytics.mockReturnValue({
      data: {
        metrics: {
          total_datasets: 0,
          active_datasets: 0,
          total_records: 0,
          crawl_success_rate: 0,
          avg_processing_time_minutes: 0,
        },
        trends: {
          datasets_created_last_30_days: 0,
          records_processed_last_24_hours: 0,
        },
        top_domains: [],
      },
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    render(<Dashboard />);

    expect(screen.getByText('0')).toBeInTheDocument();
    expect(screen.getByText('No domains found')).toBeInTheDocument();
  });

  it('formats large numbers correctly', () => {
    mockUseAnalytics.mockReturnValue({
      data: mockAnalytics({
        metrics: {
          total_datasets: 1500,
          active_datasets: 1200,
          total_records: 2500000,
          crawl_success_rate: 0.987,
          avg_processing_time_minutes: 15.75,
        },
      }),
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    render(<Dashboard />);

    expect(screen.getByText('1,500')).toBeInTheDocument();
    expect(screen.getByText('2.5M')).toBeInTheDocument();
    expect(screen.getByText('98.7%')).toBeInTheDocument();
    expect(screen.getByText('15.8 min')).toBeInTheDocument();
  });

  it('shows recent activity trends', () => {
    mockUseAnalytics.mockReturnValue({
      data: mockAnalytics({
        trends: {
          datasets_created_last_30_days: 15,
          records_processed_last_24_hours: 125000,
        },
      }),
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    render(<Dashboard />);

    expect(screen.getByText('Recent Activity')).toBeInTheDocument();
    expect(screen.getByText('15 datasets created')).toBeInTheDocument();
    expect(screen.getByText('125K records processed')).toBeInTheDocument();
  });

  it('is accessible with proper ARIA labels', () => {
    mockUseAnalytics.mockReturnValue({
      data: mockAnalytics(),
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    render(<Dashboard />);

    expect(screen.getByRole('main')).toHaveAttribute('aria-label', 'Dashboard');
    expect(screen.getByRole('region', { name: 'Analytics Overview' })).toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'Top Domains' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /refresh analytics/i })).toBeInTheDocument();
  });

  it('updates when analytics data changes', async () => {
    const { rerender } = render(<Dashboard />);

    // Initial state
    mockUseAnalytics.mockReturnValue({
      data: mockAnalytics({ metrics: { total_datasets: 5 } }),
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    rerender(<Dashboard />);
    expect(screen.getByText('5')).toBeInTheDocument();

    // Updated state
    mockUseAnalytics.mockReturnValue({
      data: mockAnalytics({ metrics: { total_datasets: 10 } }),
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    rerender(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument();
    });
  });
});
