import { useEffect, useState } from 'react';
import { useAuth } from './hooks/useAuth';
import LoginForm from './components/Auth/LoginForm';
import Dashboard from './components/Dashboard/Dashboard';

function App() {
  const { isAuthenticated, isLoading, user, error, checkAuth, logout } = useAuth();
  const [currentPath, setCurrentPath] = useState(window.location.pathname);
  
  // Debug authentication and routing
  console.log('Auth state:', { isAuthenticated, isLoading, currentPath, user, error });
  
  // Handle authentication after redirect from backend
  useEffect(() => {
    const isRedirectFromAuth =
      currentPath === '/dashboard' &&
      document.referrer.includes('localhost:8001');

    if (isRedirectFromAuth && !isAuthenticated && !isLoading) {
      console.log('Detected redirect from auth, running checkAuth');
      checkAuth();
    }
  }, [currentPath, isAuthenticated, isLoading, checkAuth]);

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

  // Trigger logout when navigating to /logout
  useEffect(() => {
    if (currentPath === '/logout') {
      logout();
    }
  }, [currentPath, logout]);

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

  if (currentPath === '/logout') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-gray-600">Signing out...</p>
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
