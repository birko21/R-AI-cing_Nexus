# Tactical Track metadata contract

This is the Phase 0 boundary between race data and the Tactical Track renderer. The lab consumes `window.NEXUS_TACTICAL_FIXTURE`; production should supply the same normalized shape from a provider adapter.

```ts
type TacticalTrackFixture = {
  schemaVersion: 'nexus.tactical-track.fixture.v1';
  source: {
    kind: 'synthetic' | 'provider';
    id: string;
    live: boolean;
    providerActivated: boolean;
  };
  race: {
    meeting: string;
    race: string;
    code: 'THOROUGHBRED' | 'HARNESS' | 'GREYHOUND';
    distanceMeters: number;
    view: 'EARLY_SETTLING_0_400M';
  };
  entries: Array<{
    number: number;
    name: string;
    color: string;
    group: 'LEAD' | 'ON PACE' | 'MIDFIELD' | 'BACKMARKERS';
    detail: string;
    factor: string;
    silks: {
      source: 'synthetic-local' | 'provider-normalized' | 'owner-approved';
      asset: string;
      label: string;
      primary: string;
      secondary: string;
      pattern: string;
    };
  }>;
  scenarios: Record<'base' | 'contested', {
    positions: Record<string, [xPercent: number, yPercent: number, scale: 1]>;
  }>;
};
```

## Betfair/provider adapter boundary

The renderer must not know Betfair response shapes. An adapter should map the available provider silk image/colour/pattern fields into `entries[].silks`, validate the asset URL or cache key, and preserve a rights/source record. If a silk asset is unavailable or not cleared, the adapter must return an explicit placeholder state rather than silently inventing a live-looking silk.

The current fixture is deliberately synthetic:

- `source.id` is `synthetic://betfair/mock-v1`;
- `source.live` and `source.providerActivated` are `false`;
- local generated runner images are marked `synthetic-local`;
- no provider credentials, network calls, live odds, or wagering behavior are involved.
