# ADR-0004: Entitlement-aware source adapters and controlled scraping

- **Status:** Accepted with G0–G3 deferral
- **Date:** 10 October 2026
- **Scope:** Provider adapters and public-web collection

## Decision

Source adapters are read-only, capability-reporting and disableable. Every source operation is checked against an entitlement record covering access, storage, retention, model use, display, export and third-party transfer.

Public scraping is permitted only for publicly accessible content where the intended use is technically and legally appropriate. Scrapers must respect robots/terms/rate limits and must not bypass authentication, paywalls, CAPTCHAs, anti-bot controls, geographic restrictions or other access controls. Retrieval URL, timestamp, checksum, parser version and source mode are mandatory.

The active v1.1 MVP remains offline and synthetic-only. Scraping cannot be enabled in G0–G3 merely because the execution prompt permits a later controlled adapter.

## Consequences

- An unavailable or unapproved source produces `NOT_AVAILABLE`/`NOT_ENTITLED`, never a successful empty response or fabricated value.
- Parser drift, 403/429 responses and rights uncertainty quarantine data and can trigger a source kill switch.
- Provider-specific work requires a later entitlement and reconciliation checkpoint.

