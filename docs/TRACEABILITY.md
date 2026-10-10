# Requirements traceability

This matrix maps the supplied v1.1 source requirements to the implementation backlog. Ticket IDs refer to [`docs/backlog/TICKETS.md`](backlog/TICKETS.md) and corresponding GitHub issues.

| Requirement | Source | Verification/evidence | Tickets |
|---|---|---|---|
| Three-code navigation and domain separation | Master v1.1 Objective/Architecture | Cross-code fixture and E2E journeys | RIL-011, RIL-016–020 |
| Offline, synthetic-only, non-wagering MVP | Master v1.1 Objective/Conflict resolution | Data-mode banners, no-order scan, G0–G3 checkpoints | RIL-001, RIL-016, RIL-020, RIL-025 |
| Repository source-of-truth and conflict precedence | Master v1.1 Documents/Conflict resolution | Imported hashes and source manifest | RIL-001, RIL-002 |
| Authenticated API with anonymous status only | Master v1.1 Authentication boundary | Auth matrix and negative route tests | RIL-009, RIL-010, RIL-056 |
| Loopback-only development auth and fail-closed external bind | Execution Prompt Required technology | Startup and bind-mode tests | RIL-006, RIL-010 |
| Bounded pagination and non-forgeable cursors | Master v1.1 Pagination and time | Contract and cursor mismatch tests | RIL-007, RIL-009 |
| UTC persistence and Australia/Sydney presentation | Master v1.1 Pagination and time | Timezone/unit tests and UI evidence | RIL-013, RIL-017, RIL-018 |
| Immutable source receipts and provenance | Master v1.1 Provenance | Hash, receipt and replay tests | RIL-014, RIL-033 |
| Append-only corrections, forecasts and selections | Master v1.1 Provenance | Revision and immutability tests | RIL-012, RIL-024, RIL-025, RIL-041, RIL-042 |
| B0/B1 illustrative baseline only | Master v1.1 Model and science | Deterministic model tests and status labels | RIL-021–025 |
| Point-in-time cutoff integrity | Master v1.1 Model and science | Future-leak injection and replay tests | RIL-013, RIL-026, RIL-027 |
| Coupled-entry abstention and tie exclusion | Master v1.1 Conflict resolution/Model | Edge-case forecast and scoring tests | RIL-025, RIL-028 |
| G0 repository/governance baseline | Execution Prompt G0 | Source manifest, decisions, traceability, risks | RIL-001–005 |
| G1 database/API/auth foundation | Execution Prompt G1 | Migration, API, idempotency and auth evidence | RIL-006–015 |
| G2 accessible three-code UI | Execution Prompt G2 | Playwright, screenshots and accessibility checks | RIL-017–020 |
| G3 forecasts, manifests, scoring and replay | Execution Prompt G3 | Forecast hashes, Brier/log loss, scratching and leakage tests | RIL-021–030 |
| Later public scraping/provider rights | Execution Prompt Authorisations / E6 | Source-specific entitlement and adapter checkpoint | RIL-031–035 |
| No automatic model promotion | Master v1.1 Model and science | Independent assurance and registry tests | RIL-028–030, RIL-055 |
| Pilot security, DR and cost controls | Master v1.1 Functional acceptance / E11 | Release checklist, restore and budget evidence | RIL-056–060 |

## Traceability status

- Active G0 requirements: mapped.
- G1–G3 requirements: mapped to backlog; contracts and tests not yet implemented.
- G4–G11 requirements: retained as gated future work; no claim of completion.

