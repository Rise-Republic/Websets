import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import AppLayout from './components/layout/AppLayout';
import EnterpriseLogin from './components/Auth/EnterpriseLogin';
import AuthCallback from './components/Auth/AuthCallback';
import { DevAuth } from './components/Auth/DevAuth';
import Dashboard from './components/Dashboard/Dashboard';
import SearchInterface from './components/Search/SearchInterface';
import UserSettings from './components/Settings/UserSettings';

const App: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [devUser, setDevUser] = useState<any>(null);

  // Check if WorkOS is configured
  const workosClientId = import.meta.env.VITE_WORKOS_CLIENT_ID;
  const isWorkOSConfigured = workosClientId && workosClientId !== 'client_01HXRMBQ9BJ3E7QSTQ9X2PHVB7';

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Development mode - bypass WorkOS
  if (!isWorkOSConfigured && !devUser) {
    return <DevAuth onLogin={(user) => setDevUser(user)} />;
  }

  // Production mode with WorkOS
  if (isWorkOSConfigured && !isAuthenticated) {
    return (
      <Routes>
        <Route path="/auth/workos/callback" element={<AuthCallback />} />
        <Route path="*" element={<EnterpriseLogin />} />
      </Routes>
    );
  }

  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/search" element={<SearchInterface />} />
        <Route path="/settings" element={<UserSettings />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AppLayout>
  );
}

export default App;
