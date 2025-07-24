import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import DatasetList from './DatasetList';
import * as api from '@/services/api';

jest.mock('@/services/api');
const mockApi = api as jest.Mocked<typeof api>;

const datasets = [
  { id: '1', name: 'DS1', description: '', record_count: 2, created_at: '2024-01-01T00:00:00Z', job_id: 'j1' },
  { id: '2', name: 'DS2', description: '', record_count: 5, created_at: '2024-01-02T00:00:00Z', job_id: 'j2' }
] as api.Dataset[];

mockApi.apiService.getDatasets.mockResolvedValue(datasets);
(mockApi as any).default = mockApi.apiService;


describe('DatasetList', () => {
  test('renders datasets from API', async () => {
    render(<DatasetList />);

    await waitFor(() => {
      expect(mockApi.apiService.getDatasets).toHaveBeenCalled();
    });

    for (const ds of datasets) {
      expect(await screen.findByText(ds.name)).toBeInTheDocument();
    }
  });
});
