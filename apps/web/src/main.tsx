import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { Auth0App, AuthConfigurationRequired, readAuthConfig } from './auth';
import './styles.css';

const auth = readAuthConfig();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {!auth.required && <App />}
    {auth.required && !auth.config && <AuthConfigurationRequired message={auth.error} />}
    {auth.required && auth.config && <Auth0App config={auth.config} />}
  </StrictMode>,
);
