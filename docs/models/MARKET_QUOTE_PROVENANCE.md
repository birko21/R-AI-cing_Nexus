# Market-selection and quote provenance

RIL-036 defines paper-analysis quote storage without creating a wagering or order path. A quote is accepted only with an exact mapping containing the racing code, race ID, field revision, entry ID, market source/ID, and selection ID. Name-only mapping is quarantined.

Each accepted quote stores its market type, declared price type, price, source timestamp, retrieval timestamp, in-play status, size, liquidity, entitlement reference, source receipt ID, data mode, and rights state. Timestamps are timezone-aware and a source timestamp cannot be later than retrieval.

Synthetic quotes require `SYNTHETIC` rights. Licensed quotes require approved rights. Public or licensed data remains explicitly labelled and tied to an entitlement reference; a quote is never treated as official or licensed merely because it exists.

The SQL migration is append-only for both quotes and mapping quarantine records. The checked-in fixture is synthetic and offline. It demonstrates a valid exact mapping and a quarantined name-only mapping; it does not contain live odds and does not expose order placement, bookmaker credentials, or staking operations.
