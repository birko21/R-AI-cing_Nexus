import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import App, { liveCommandItems } from './App';
import { authFailureCopy } from './auth';

describe('authenticated dashboard hand-off', () => {
  it('renders the research dashboard after the authenticated boundary', () => {
    const markup = renderToStaticMarkup(
      <App apiRequest={async () => new Response(null, { status: 200 })} />,
    );

    expect(markup).toContain('Today / Command Centre');
    expect(markup).toContain('DEMO ONLY');
    expect(markup).not.toContain('Protected staging configuration required');
  });

  it('maps licensed canonical meetings to live provider cards', () => {
    const cards = liveCommandItems([{
      meeting_id: 'punters-edge:meeting:randwick',
      code: 'THOROUGHBRED',
      name: 'Randwick',
      country: 'AUS',
      scheduled_date: '2026-10-15T04:00:00Z',
      data_mode: 'LICENSED',
    }]);

    expect(cards).toHaveLength(1);
    expect(cards[0]).toMatchObject({
      status: 'LIVE',
      label: 'Thoroughbred',
      meeting: 'Randwick',
      sourceAge: 'Canonical licensed receipt',
    });
    expect(cards[0].note).not.toContain('fictional');
  });

  it('distinguishes an API authentication rejection from token expiry', () => {
    expect(authFailureCopy('rejected').title).toBe('Nexus API authentication rejected');
    expect(authFailureCopy('rejected').message).not.toContain('expired');
    expect(authFailureCopy('expired').title).toBe('Nexus session expired');
  });
});
