import { useEffect, useState } from 'react';
import { useAuth } from './hooks/useAuth';
import LoginForm from './components/Auth/LoginForm';
import Dashboard from './components/Dashboard/Dashboard';

function App() {
  const { isAuthenticated, isLoading, user, error } = useAuth();
  const [currentPath, setCurrentPath] = useState(window.location.pathname);
  const [forceReload, setForceReload] = useState(false);
  
  // Debug authentication and routing
  console.log('Auth state:', { isAuthenticated, isLoading, currentPath, user, error });
  
  // Handle authentication after redirect from backend
  useEffect(() => {
    const isRedirectFromAuth = 
      currentPath === '/dashboard' && 
      document.referrer.includes('localhost:8001');
      
    if (isRedirectFromAuth && !isAuthenticated && !isLoading) {
      console.log('Detected redirect from auth, triggering reload');
      // Force a reload to re-check authentication
      setForceReload(true);
    }
  }, [currentPath, isAuthenticated, isLoading]);
  
  // Trigger a page reload if needed
  useEffect(() => {
    if (forceReload) {
      window.location.reload();
    }
  }, [forceReload]);

  // Handle routing based on URL path
  useEffect(() => {
    const handleRouteChange = () => {
      setCurrentPath(window.location.pathname);
    };

    // Listen for popstate events (back/forward navigation)
    window.addEventListener('popstate', handleRouteChange);
    
    return () => {
      window.removeEventListener('popstate', handleRouteChange);
    };
  }, []);

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

  // If user is authenticated and on /dashboard path, show Dashboard
  if (isAuthenticated && currentPath === '/dashboard') {
    return <Dashboard />;
  }
  
  // If user is authenticated but on root path, redirect to dashboard
  if (isAuthenticated && currentPath === '/') {
    window.history.pushState({}, '', '/dashboard');
    setCurrentPath('/dashboard');
    return <Dashboard />;
  }

  // Otherwise show login form
  return <LoginForm />;
}

export default App;
