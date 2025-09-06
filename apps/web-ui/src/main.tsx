import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import AuthProvider from './hooks/useAuth';
import { AuthKitProvider } from '@workos-inc/authkit-react';
import App from './App.tsx';
import './index.css';

// Get the redirect URI from environment variables or default to the frontend callback route
const redirectUri =
  import.meta.env.VITE_WORKOS_REDIRECT_URI ||
  'http://localhost:3000/auth/workos/callback';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthKitProvider
      clientId={import.meta.env.VITE_WORKOS_CLIENT_ID}
      redirectUri={redirectUri}
    >
      <AuthProvider>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </AuthProvider>
    </AuthKitProvider>
  </StrictMode>
);
