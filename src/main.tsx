import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import AuthProvider from './hooks/useAuth';
import { AuthKitProvider } from '@workos-inc/authkit-react';
import App from './App.tsx';
import './index.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthKitProvider clientId={import.meta.env.VITE_WORKOS_CLIENT_ID}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </AuthKitProvider>
  </StrictMode>
);
