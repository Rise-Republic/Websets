import React from 'react';
import { useAuth } from '@workos-inc/authkit-react';

const LoginForm: React.FC = () => {
  const { signIn } = useAuth();

  const handleSignIn = () => {
    console.log('Redirecting to WorkOS AuthKit...');
    signIn();
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to Websets
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Secure authentication powered by WorkOS AuthKit
          </p>
        </div>
        <div className="mt-8">
          <button
            type="button"
            onClick={handleSignIn}
            className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors cursor-pointer"
          >
            🔐 Sign in with AuthKit
          </button>
        </div>
      </div>
    </div>
  );
};

export default LoginForm;
