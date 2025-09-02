/**
 * Unit Tests for DatasetList Component
 * Testing dataset listing, filtering, and management functionality
 */

import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render, mockDataset } from '../utils/testHelpers';
import DatasetList from '../../components/Datasets/DatasetList';

// Mock the datasets hook
jest.mock('../../hooks/useDatasets', () => ({
  useDatasets: jest.fn(),
}));

import { useDatasets } from '../../hooks/useDatasets';
const mockUseDatasets = useDatasets as jest.MockedFunction<typeof useDatasets>;

describe('DatasetList Component', () => {
  const mockDatasets = [
    mockDataset({ id: 1, name: 'E-commerce Dataset', status: 'active', record_count: 15000 }),
    mockDataset({ id: 2, name: 'News Articles', status: 'processing', record_count: 8500 }),
    mockDataset({ id: 3, name: 'Research Papers', status: 'inactive', record_count: 25000 }),
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders dataset list with data', () => {
    mockUseDatasets.mockReturnValue({
      datasets: mockDatasets,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      createDataset: jest.fn(),
      updateDataset: jest.fn(),
      deleteDataset: jest.fn(),
    });

    render(<DatasetList />);

    expect(screen.getByText('Datasets')).toBeInTheDocument();
    expect(screen.getByText('E-commerce Dataset')).toBeInTheDocument();
    expect(screen.getByText('News Articles')).toBeInTheDocument();
    expect(screen.getByText('Research Papers')).toBeInTheDocument();
  });

  it('shows loading state while fetching datasets', () => {
    mockUseDatasets.mockReturnValue({
      datasets: [],
      isLoading: true,
      error: null,
      refetch: jest.fn(),
      createDataset: jest.fn(),
      updateDataset: jest.fn(),
      deleteDataset: jest.fn(),
    });

    render(<DatasetList />);

    expect(screen.getByText('Loading datasets...')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('displays error state when datasets fail to load', () => {
    const mockError = new Error('Failed to fetch datasets');
    mockUseDatasets.mockReturnValue({
      datasets: [],
      isLoading: false,
      error: mockError,
      refetch: jest.fn(),
      createDataset: jest.fn(),
      updateDataset: jest.fn(),
      deleteDataset: jest.fn(),
    });

    render(<DatasetList />);

    expect(screen.getByText('Error loading datasets')).toBeInTheDocument();
    expect(screen.getByText('Failed to fetch datasets')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('shows empty state when no datasets exist', () => {
    mockUseDatasets.mockReturnValue({
      datasets: [],
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      createDataset: jest.fn(),
      updateDataset: jest.fn(),
      deleteDataset: jest.fn(),
    });

    render(<DatasetList />);

    expect(screen.getByText('No datasets found')).toBeInTheDocument();
    expect(screen.getByText('Create your first dataset to get started')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create dataset/i })).toBeInTheDocument();
  });

  it('filters datasets by status', async () => {
    mockUseDatasets.mockReturnValue({
      datasets: mockDatasets,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      createDataset: jest.fn(),
      updateDataset: jest.fn(),
      deleteDataset: jest.fn(),
    });

    const user = userEvent.setup();
    render(<DatasetList />);

    // Filter by active status
    const statusFilter = screen.getByLabelText(/filter by status/i);
    await user.selectOptions(statusFilter, 'active');

    expect(screen.getByText('E-commerce Dataset')).toBeInTheDocument();
    expect(screen.queryByText('News Articles')).not.toBeInTheDocument();
    expect(screen.queryByText('Research Papers')).not.toBeInTheDocument();
  });

  it('searches datasets by name', async () => {
    mockUseDatasets.mockReturnValue({
      datasets: mockDatasets,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      createDataset: jest.fn(),
      updateDataset: jest.fn(),
      deleteDataset: jest.fn(),
    });

    const user = userEvent.setup();
    render(<DatasetList />);

    const searchInput = screen.getByPlaceholderText(/search datasets/i);
    await user.type(searchInput, 'news');

    await waitFor(() => {
      expect(screen.getByText('News Articles')).toBeInTheDocument();
      expect(screen.queryByText('E-commerce Dataset')).not.toBeInTheDocument();
      expect(screen.queryByText('Research Papers')).not.toBeInTheDocument();
    });
  });

  it('sorts datasets by different criteria', async () => {
    mockUseDatasets.mockReturnValue({
      datasets: mockDatasets,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      createDataset: jest.fn(),
      updateDataset: jest.fn(),
      deleteDataset: jest.fn(),
    });

    const user = userEvent.setup();
    render(<DatasetList />);

    const sortSelect = screen.getByLabelText(/sort by/i);
    await user.selectOptions(sortSelect, 'record_count');

    // Verify datasets are sorted by record count (descending)
    const datasetElements = screen.getAllByTestId('dataset-item');
    expect(datasetElements[0]).toHaveTextContent('Research Papers'); // 25000 records
    expect(datasetElements[1]).toHaveTextContent('E-commerce Dataset'); // 15000 records
    expect(datasetElements[2]).toHaveTextContent('News Articles'); // 8500 records
  });

  it('opens create dataset modal', async () => {
    mockUseDatasets.mockReturnValue({
      datasets: mockDatasets,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      createDataset: jest.fn(),
      updateDataset: jest.fn(),
      deleteDataset: jest.fn(),
    });

    const user = userEvent.setup();
    render(<DatasetList />);

    const createButton = screen.getByRole('button', { name: /create dataset/i });
    await user.click(createButton);

    expect(screen.getByText('Create New Dataset')).toBeInTheDocument();
    expect(screen.getByLabelText(/dataset name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
  });

  it('deletes dataset with confirmation', async () => {
    const mockDeleteDataset = jest.fn();
    mockUseDatasets.mockReturnValue({
      datasets: mockDatasets,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      createDataset: jest.fn(),
      updateDataset: jest.fn(),
      deleteDataset: mockDeleteDataset,
    });

    const user = userEvent.setup();
    render(<DatasetList />);

    // Click delete button for first dataset
    const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
    await user.click(deleteButtons[0]);

    // Confirm deletion
    expect(screen.getByText('Confirm Deletion')).toBeInTheDocument();
    const confirmButton = screen.getByRole('button', { name: /confirm delete/i });
    await user.click(confirmButton);

    expect(mockDeleteDataset).toHaveBeenCalledWith(1);
  });

  it('displays dataset status badges correctly', () => {
    mockUseDatasets.mockReturnValue({
      datasets: mockDatasets,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      createDataset: jest.fn(),
      updateDataset: jest.fn(),
      deleteDataset: jest.fn(),
    });

    render(<DatasetList />);

    expect(screen.getByText('active')).toHaveClass('status-active');
    expect(screen.getByText('processing')).toHaveClass('status-processing');
    expect(screen.getByText('inactive')).toHaveClass('status-inactive');
  });

  it('shows record counts with proper formatting', () => {
    mockUseDatasets.mockReturnValue({
      datasets: mockDatasets,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      createDataset: jest.fn(),
      updateDataset: jest.fn(),
      deleteDataset: jest.fn(),
    });

    render(<DatasetList />);

    expect(screen.getByText('15,000 records')).toBeInTheDocument();
    expect(screen.getByText('8,500 records')).toBeInTheDocument();
    expect(screen.getByText('25,000 records')).toBeInTheDocument();
  });

  it('is accessible with proper ARIA labels', () => {
    mockUseDatasets.mockReturnValue({
      datasets: mockDatasets,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      createDataset: jest.fn(),
      updateDataset: jest.fn(),
      deleteDataset: jest.fn(),
    });

    render(<DatasetList />);

    expect(screen.getByRole('main')).toHaveAttribute('aria-label', 'Datasets');
    expect(screen.getByRole('searchbox')).toHaveAccessibleName('Search datasets');
    expect(screen.getByRole('combobox', { name: /filter by status/i })).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: /sort by/i })).toBeInTheDocument();
  });

  it('handles pagination correctly', async () => {
    const manyDatasets = Array.from({ length: 25 }, (_, i) => 
      mockDataset({ id: i + 1, name: `Dataset ${i + 1}` })
    );

    mockUseDatasets.mockReturnValue({
      datasets: manyDatasets,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      createDataset: jest.fn(),
      updateDataset: jest.fn(),
      deleteDataset: jest.fn(),
    });

    const user = userEvent.setup();
    render(<DatasetList />);

    // Should show first 20 datasets
    expect(screen.getByText('Dataset 1')).toBeInTheDocument();
    expect(screen.getByText('Dataset 20')).toBeInTheDocument();
    expect(screen.queryByText('Dataset 21')).not.toBeInTheDocument();

    // Navigate to next page
    const nextButton = screen.getByRole('button', { name: /next page/i });
    await user.click(nextButton);

    expect(screen.getByText('Dataset 21')).toBeInTheDocument();
    expect(screen.getByText('Dataset 25')).toBeInTheDocument();
    expect(screen.queryByText('Dataset 1')).not.toBeInTheDocument();
  });

  it('refreshes dataset list', async () => {
    const mockRefetch = jest.fn();
    mockUseDatasets.mockReturnValue({
      datasets: mockDatasets,
      isLoading: false,
      error: null,
      refetch: mockRefetch,
      createDataset: jest.fn(),
      updateDataset: jest.fn(),
      deleteDataset: jest.fn(),
    });

    const user = userEvent.setup();
    render(<DatasetList />);

    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    await user.click(refreshButton);

    expect(mockRefetch).toHaveBeenCalledTimes(1);
  });
});
