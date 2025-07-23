import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import DatasetViewer from './DatasetViewer';
import * as api from '../../services/api';

jest.mock('../../services/api');
const mockApi = api as jest.Mocked<typeof api>;

const dataset = { id: '1', name: 'DS1', description: '', record_count: 2, created_at: '2024-01-01T00:00:00Z', job_id: 'j1' } as api.Dataset;
const records = [
  { id: 'r1', content: { foo: 'bar' }, metadata: { source_url: 'http://x', source_title: 'x' }, created_at: '2024-01-01T00:00:00Z' }
] as api.DatasetRecord[];

mockApi.apiService.getDatasetRecords.mockResolvedValue(records);
(mockApi as any).default = mockApi.apiService;


describe('DatasetViewer', () => {
  test('loads and displays records', async () => {
    render(<DatasetViewer dataset={dataset} onClose={jest.fn()} />);

    await waitFor(() => {
      expect(mockApi.apiService.getDatasetRecords).toHaveBeenCalledWith(dataset.id);
    });

    expect(await screen.findByText('bar')).toBeInTheDocument();
  });
});
