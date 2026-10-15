import { useCallback, useState, type ReactNode } from 'react';
import { Auth0Provider, useAuth0, type User } from '@auth0/auth0-react';

import App, { NexusMark, type NexusApiRequest } from './App';

export type AuthConfig = {
  domain: string;
  clientId: string;
  audience: string;
  apiBaseUrl: string;
  allowedSubject: string;
};

type AuthConfigResult = { required: false } | { required: true; config?: AuthConfig; error?: string };
export type NexusAuthFailure = 'expired' | 'rejected';

export function authFailureCopy(failure: NexusAuthFailure): { title: string; message: string } {
  if (failure === 'rejected') {
    return {
      title: 'Nexus API authentication rejected',
      message: 'The API did not accept the current access token. Sign in again before continuing.',
    };
  }
  return {
    title: 'Nexus session expired',
    message: 'The Auth0 session or access token expired. Sign in again before continuing.',
  };
}

export function readAuthConfig(): AuthConfigResult {
  if (import.meta.env.VITE_AUTH_REQUIRED !== 'true') {
    return { required: false };
  }
  const values = {
    domain: import.meta.env.VITE_AUTH0_DOMAIN?.trim() ?? '',
    clientId: import.meta.env.VITE_AUTH0_CLIENT_ID?.trim() ?? '',
    audience: import.meta.env.VITE_AUTH0_AUDIENCE?.trim() ?? '',
    apiBaseUrl: import.meta.env.VITE_API_BASE_URL?.trim().replace(/\/$/, '') ?? '',
    allowedSubject: import.meta.env.VITE_AUTH0_ALLOWED_SUBJECT?.trim() ?? '',
  };
  const missing = Object.entries(values)
    .filter(([, value]) => !value)
    .map(([key]) => key);
  if (missing.length > 0) {
    return { required: true, error: `Missing protected staging configuration: ${missing.join(', ')}` };
  }
  return { required: true, config: values };
}

export function Auth0App({ config }: { config: AuthConfig }) {
  return (
    <Auth0Provider
      domain={config.domain}
      clientId={config.clientId}
      cacheLocation="memory"
      useRefreshTokens={false}
      authorizationParams={{
        audience: config.audience,
        scope: 'openid profile email races:read forecasts:read selections:read selections:write',
        redirect_uri: `${window.location.origin}/callback`,
      }}
    >
      <AuthenticationBoundary config={config} />
    </Auth0Provider>
  );
}

function AuthenticationBoundary({ config }: { config: AuthConfig }) {
  const { error, isAuthenticated, isLoading, loginWithRedirect, logout, user } = useAuth0();

  if (isLoading) {
    return <AuthState title="Checking owner session" message="Validating the Auth0 session before loading Nexus." />;
  }
  if (error) {
    return <AuthState title="Sign-in could not be completed" message="The Nexus session is invalid or expired. Sign in again to continue." action={<button type="button" onClick={() => void loginWithRedirect()}>Try sign in again</button>} />;
  }
  if (!isAuthenticated || !user) {
    return <AuthState title="Nexus owner sign-in required" message="Only the explicitly allowlisted owner identity may access this private staging application." action={<button type="button" onClick={() => void loginWithRedirect()}>Sign in with Auth0</button>} />;
  }
  if (user.sub !== config.allowedSubject) {
    return <AuthState title="Owner access denied" message="This Auth0 identity is not allowlisted for Nexus." action={<button type="button" onClick={() => void logout({ logoutParams: { returnTo: window.location.origin } })}>Sign out</button>} />;
  }
  return <AuthenticatedApp config={config} user={user} />;
}

function AuthenticatedApp({ config, user }: { config: AuthConfig; user: User }) {
  const [authFailure, setAuthFailure] = useState<NexusAuthFailure | null>(null);
  const { logout } = useAuth0();
  const onAuthFailure = useCallback((failure: NexusAuthFailure) => setAuthFailure(failure), []);
  const request = useNexusApiRequest(config, onAuthFailure);

  if (authFailure) {
    const copy = authFailureCopy(authFailure);
    return <AuthState title={copy.title} message={copy.message} action={<button type="button" onClick={() => void logout({ logoutParams: { returnTo: window.location.origin } })}>Sign in again</button>} />;
  }

  return (
    <>
      <nav className="auth-toolbar" aria-label="Owner session">
        <span>Owner session active</span>
        <button type="button" onClick={() => void logout({ logoutParams: { returnTo: window.location.origin } })}>Sign out</button>
      </nav>
      <App apiRequest={request} />
    </>
  );
}

function useNexusApiRequest(config: AuthConfig, onAuthFailure: (failure: NexusAuthFailure) => void): NexusApiRequest {
  const { getAccessTokenSilently } = useAuth0();
  return useCallback(async (path, init, requiredScope = 'races:read') => {
    let token: string;
    try {
      const resolvedToken = await getAccessTokenSilently({
        authorizationParams: { audience: config.audience, scope: `openid ${requiredScope}` },
      });
      if (!resolvedToken) {
        throw new Error('Nexus access token was not returned');
      }
      token = resolvedToken;
    } catch {
      onAuthFailure('expired');
      throw new Error('Nexus session expired');
    }
    const headers = new Headers(init?.headers);
    headers.set('Authorization', `Bearer ${token}`);
    const response = await fetch(`${config.apiBaseUrl}${path}`, { ...init, headers });
    if (response.status === 401) {
      onAuthFailure('rejected');
    }
    return response;
  }, [config.apiBaseUrl, config.audience, getAccessTokenSilently, onAuthFailure]);
}

function AuthState({ title, message, action }: { title: string; message: string; action?: ReactNode }) {
  return (
    <main className="shell auth-state auth-gate" aria-live="polite">
      <div className="auth-gate-grid">
        <div className="auth-gate-brand"><NexusMark /><div><p className="eyebrow">RACING INTELLIGENCE LAB</p><div className="brand-wordmark">NEXUS <span>/ RESEARCH OS</span></div><p className="auth-gate-tagline">Evidence before inference.</p></div></div>
        <section className="auth-gate-card" aria-labelledby="auth-state-title">
          <div className="auth-gate-card-top"><span className="session-pulse" aria-hidden="true" /><span>PRIVATE OWNER ACCESS</span></div>
          <p className="eyebrow">SECURE WORKSPACE</p>
          <h1 id="auth-state-title">{title}</h1>
          <p>{message}</p>
          {action && <div className="auth-action">{action}</div>}
          <div className="auth-gate-boundary"><span>READ-ONLY RESEARCH</span><span>NO WAGERING</span><span>PROVENANCE FIRST</span></div>
        </section>
      </div>
    </main>
  );
}

export function AuthConfigurationRequired({ message }: { message?: string }) {
  return <AuthState title="Protected staging configuration required" message={message ?? 'Auth0 domain, client, API audience and owner allowlist must be configured before Nexus can open.'} />;
}
