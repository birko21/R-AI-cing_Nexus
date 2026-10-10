# Controlled public-scraping framework

RIL-031 defines the only supported boundary for public web retrieval. It is a policy-gated adapter, not a crawler and not a mechanism for bypassing access controls.

## Required controls

- Retrieval is HTTPS-only and limited to explicitly configured URL prefixes.
- URLs containing credentials and private, loopback, link-local, or reserved IP literals are rejected.
- A descriptive user agent identifies the research client.
- The caller must explicitly provide both robots permission and terms permission before a request is made.
- A robots checker is evaluated before retrieval.
- Timeout, minimum inter-request delay, and retry limits are bounded by policy.
- A kill switch blocks all retrieval immediately.
- Authentication, paywall, anti-bot, conflict, and legal restriction responses are not retried or bypassed.
- Only successful 2xx responses are accepted.

## Provenance

Every accepted response produces a `ScrapeEnvelope` with the source URL, UTC retrieval time, response status, payload SHA-256, payload size, user agent, attempt count, and `SCRAPED_PUBLIC` data mode. Rights are initially recorded as `UNASSESSED`; later tickets must not promote that state silently.

The synthetic policy fixture is configuration evidence only. It uses a reserved example URL and does not enable or perform a live scrape. Tests inject a mock transport so CI remains deterministic and offline.

## Operating rule

Public availability does not imply permission to collect, retain, or redistribute data. A real provider requires a separate approved adapter and source record. If the provider blocks access or permission cannot be established, the system fails closed and records the reason rather than attempting a workaround.
