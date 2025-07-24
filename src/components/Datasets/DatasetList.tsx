import React, { useEffect, useState } from 'react';
import apiService, { Dataset } from '@/services/api';

interface DatasetListProps {
  onDatasetSelect?: (dataset: Dataset) => void;
}

const DatasetList: React.FC<DatasetListProps> = ({ onDatasetSelect }) => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDatasets = async () => {
    try {
      setLoading(true);
      const data = await apiService.getDatasets();
      setDatasets(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load datasets');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDatasets();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="bg-white">
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <h2 className="text-lg font-medium text-gray-900">Datasets</h2>
        <button onClick={loadDatasets} className="text-sm text-gray-600 hover:text-gray-800">
          Refresh
        </button>
      </div>
      {error && (
        <div className="px-6 py-4 bg-red-50 text-red-700 text-sm">{error}</div>
      )}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Records
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {datasets.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-6 py-12 text-center text-sm text-gray-500">
                  No datasets found
                </td>
              </tr>
            ) : (
              datasets.map(ds => (
                <tr
                  key={ds.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => onDatasetSelect?.(ds)}
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {ds.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {ds.record_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(ds.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DatasetList;
