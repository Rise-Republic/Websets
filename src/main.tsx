import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import AuthProvider from './hooks/useAuth';
import { AuthKitProvider } from '@workos-inc/authkit-react';
import App from './App.tsx';
import './index.css';

// Get the redirect URI from environment variables or use the hardcoded value
const redirectUri = import.meta.env.VITE_WORKOS_REDIRECT_URI || "http://localhost:8001/api/auth/callback";

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthKitProvider 
      clientId={import.meta.env.VITE_WORKOS_CLIENT_ID}
      redirectUri={redirectUri}
    >
      <AuthProvider>
        <App />
      </AuthProvider>
    </AuthKitProvider>
  </StrictMode>
);
