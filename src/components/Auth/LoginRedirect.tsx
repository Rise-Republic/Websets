import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

const LoginRedirect = () => {
  const navigate = useNavigate();
  const { checkAuth, isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    checkAuth().then(() => {
      navigate(isAuthenticated ? '/dashboard' : '/', { replace: true });
    });
  }, [checkAuth, isAuthenticated, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <p className="text-gray-700">
        {isLoading ? 'Checking session…' : 'Redirecting…'}
      </p>
    </div>
  );
};

export default LoginRedirect;
