import React from 'react';
import { useAuth } from '@/hooks/useAuth';

const LoginForm: React.FC = () => {
  const { login } = useAuth();
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <button
        onClick={() => login()}
        className="px-6 py-3 rounded-md bg-blue-600 text-white"
      >
        Sign in with Auth0
      </button>
    </div>
  );
};

export default LoginForm;
