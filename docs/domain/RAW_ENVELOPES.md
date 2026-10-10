# Raw envelopes and quarantine

Raw inputs are accepted only as immutable envelopes containing a source identifier, canonical payload checksum, schema version, retrieval metadata, observation/publication timestamps, explicit data mode, rights state and (for licensed data) a licence reference.

The canonical JSON payload is hashed with SHA-256. A checksum mismatch, missing source identifier, invalid schema, unresolved identity or unassessed rights state becomes a quarantine record with a reason code; it is never silently ingested.

G0–G3 fixtures use `SYNTHETIC_ONLY` with `SYNTHETIC` rights state. Public scraping and licensed feeds remain separate, labelled capabilities and do not become active by creating an envelope schema.
