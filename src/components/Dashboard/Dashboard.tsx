import React, { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import JobList from '../Jobs/JobList';
import { Job } from '../../services/api';

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [showCreateJob, setShowCreateJob] = useState(false);

  const handleJobSelect = (job: Job) => {
    setSelectedJob(job);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">Websets</h1>
              <span className="ml-2 text-sm text-gray-500">Mining Dashboard</span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">Welcome, {user?.full_name}</span>
              <button
                onClick={() => setShowCreateJob(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                New Job
              </button>
              <button
                onClick={logout}
                className="text-gray-500 hover:text-gray-700 text-sm"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {showCreateJob ? (
            <div className="mb-6">
              <div className="bg-white shadow rounded-lg">
                <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                  <h2 className="text-lg font-medium text-gray-900">Create New Mining Job</h2>
                  <button
                    onClick={() => setShowCreateJob(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    <div>
                      <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-2">
                        Mining Prompt
                      </label>
                      <textarea
                        id="prompt"
                        rows={4}
                        className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        placeholder="Describe what you're looking for... e.g., 'AI startups in Europe hiring ML engineers'"
                      />
                    </div>
                    <div className="flex justify-end space-x-3">
                      <button
                        onClick={() => setShowCreateJob(false)}
                        className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                      >
                        Cancel
                      </button>
                      <button
                        className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                      >
                        Start Mining
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : null}

          {selectedJob ? (
            <div className="mb-6">
              <div className="bg-white shadow rounded-lg">
                <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                  <h2 className="text-lg font-medium text-gray-900">Job Details</h2>
                  <button
                    onClick={() => setSelectedJob(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-sm font-medium text-gray-500">Prompt</h3>
                      <p className="mt-1 text-sm text-gray-900">{selectedJob.prompt}</p>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <h3 className="text-sm font-medium text-gray-500">Status</h3>
                        <p className="mt-1 text-sm text-gray-900 capitalize">{selectedJob.status}</p>
                      </div>
                      <div>
                        <h3 className="text-sm font-medium text-gray-500">Created</h3>
                        <p className="mt-1 text-sm text-gray-900">
                          {new Date(selectedJob.created_at).toLocaleString()}
                        </p>
                      </div>
                      <div>
                        <h3 className="text-sm font-medium text-gray-500">Job ID</h3>
                        <p className="mt-1 text-sm text-gray-900 font-mono">{selectedJob.id}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : null}

          {/* Jobs List */}
          <div className="bg-white shadow rounded-lg">
            <JobList onJobSelect={handleJobSelect} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
