import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import App from './App';
import { authFailureCopy } from './auth';

describe('authenticated dashboard hand-off', () => {
  it('renders the research dashboard after the authenticated boundary', () => {
    expect(import.meta.env.VITE_AUTH_REQUIRED).toBe('true');
    const markup = renderToStaticMarkup(
      <App apiRequest={async () => new Response(null, { status: 200 })} />,
    );

    expect(markup).toContain('Today / Command Centre');
    expect(markup).toContain('DEMO ONLY');
    expect(markup).not.toContain('Protected staging configuration required');
  });

  it('distinguishes an API authentication rejection from token expiry', () => {
    expect(authFailureCopy('rejected').title).toBe('Nexus API authentication rejected');
    expect(authFailureCopy('rejected').message).not.toContain('expired');
    expect(authFailureCopy('expired').title).toBe('Nexus session expired');
  });
});
