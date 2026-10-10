# Scraped-source provenance, retention and replay

RIL-033 adds the receipt layer required after a public adapter retrieves content. It does not make public data licensed, official, current, or suitable for model evaluation by default.

## Stored receipt

Each receipt stores the retrieval URL, UTC retrieval timestamp, content SHA-256, parser version, immutable raw envelope reference, explicit `SCRAPED_PUBLIC` mode, rights state, retention deadline, and replay-fixture identifier. The common raw envelope remains the canonical payload receipt and retains its own canonical payload checksum.

Receipts and replay fixtures are append-only. A receipt cannot be replaced by a later parse, and a fixture cannot be silently changed under the same identifier. The SQL migration applies immutable-mutation triggers to both tables.

## Replay and retention

Replay reads the stored fixture, checks its content hash and parser version binding, parses it with the registered parser, and compares the resulting payload with the original raw envelope and checksum. This makes parser drift and fixture tampering visible.

Retention status is derived against a timezone-aware UTC time. Expired receipts remain visible in provenance views for audit but cannot be replayed. The view reports `ACTIVE` or `EXPIRED`, rights state, data mode, and explicit `licensed: false` and `official: false` defaults.

The checked-in fixture uses a reserved example URL and is entirely offline. It is evidence of the replay and retention contract, not evidence that a real source was accessed or approved.
