import React from 'react';
import { useAuth } from './hooks/useAuth';
import LoginForm from './components/Auth/LoginForm';
import Dashboard from './components/Dashboard/Dashboard';

function App() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Websets...</p>
        </div>
      </div>
    );
  }

  return isAuthenticated ? <Dashboard /> : <LoginForm />;
}

export default App;
