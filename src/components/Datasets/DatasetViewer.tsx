import React, { useEffect, useState } from 'react';
import apiService, { Dataset, DatasetRecord } from '../../services/api';

interface DatasetViewerProps {
  dataset: Dataset;
  onClose: () => void;
}

const DatasetViewer: React.FC<DatasetViewerProps> = ({ dataset, onClose }) => {
  const [records, setRecords] = useState<DatasetRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadRecords = async () => {
    try {
      setLoading(true);
      const data = await apiService.getDatasetRecords(dataset.id);
      setRecords(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load records');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRecords();
  }, [dataset.id]);

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <h2 className="text-lg font-medium text-gray-900">{dataset.name}</h2>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      {error && <div className="px-6 py-4 bg-red-50 text-red-700 text-sm">{error}</div>}
      {loading ? (
        <div className="p-6 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="p-6 overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Source
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Data
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {records.length === 0 ? (
                <tr>
                  <td colSpan={2} className="px-6 py-12 text-center text-sm text-gray-500">
                    No records found
                  </td>
                </tr>
              ) : (
                records.map(rec => (
                  <tr key={rec.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <a href={rec.metadata?.source_url || '#'} className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">
                        {rec.metadata?.source_title || rec.metadata?.source_url || 'Source'}
                      </a>
                    </td>
                    <td className="px-6 py-4 whitespace-pre-wrap text-sm text-gray-500">
                      <code className="whitespace-pre-wrap">{JSON.stringify(rec.content, null, 2)}</code>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default DatasetViewer;
