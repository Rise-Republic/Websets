import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import apiService from '@/services/api';

const AuthCallback = () => {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const { checkAuth } = useAuth();

  useEffect(() => {
    const code = params.get('code');
    if (!code) {
      navigate('/', { replace: true });
      return;
    }

    apiService
      .processWorkOSCallback(code)
      .then(() => checkAuth())
      .then(() => navigate('/dashboard', { replace: true }))
      .catch(() => navigate('/', { replace: true }));
  }, [params, navigate, checkAuth]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <p className="text-gray-700">Processing authentication…</p>
    </div>
  );
};

export default AuthCallback;
