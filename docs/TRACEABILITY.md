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
| Four-provider capability and licensing evidence | User roadmap / provider audit | Four-provider matrix, architecture and licensing gap report | RIL-061–064 |
| Synthetic Betfair market intelligence | User roadmap / Betfair read-only requirement | Contract adapter, catalogue/book fixture, exact runner mapping, historical prices, liquidity and SP leakage tests | RIL-065, RIL-067–068 |
| Independent three-code specialist models | User roadmap / modelling requirements | Separate code manifests, form/market/combined inputs, walk-forward ablations, calibration and assurance | RIL-069–071 |
| Fail-closed release evidence aggregation | E11 / G11 release controls | Hashed local-synthetic gate report, explicit owner/external dependencies and no activation/promotion authority | RIL-060 |
| Historical feature and evaluation foundation | RIL-061 development gate | Versioned rights-aware features, B0–B4 contracts, synthetic walk-forward evidence, explainability and readiness verdicts | RIL-061, RIL-077 |

## Traceability status

- Active G0 requirements: mapped, with repository baseline and checkpoint
  validation passing; owner/source decisions remain explicit where required.
- G1 requirements: API, contracts, authentication boundary, migrations through
  the durable ingestion lease migration, and synthetic worker tests are present.
  The disposable PostgreSQL smoke harness now validates loopback/disposable
  targeting before connecting, verifies the ingestion schema and checksums,
  runs the durable synthetic worker, and performs upgrade/downgrade/re-upgrade. Its actual execution remains
  outstanding because no approved `DATABASE_URL` has been supplied.
- G2 requirements: the synthetic three-code UI and Tactical Track proof have
  browser evidence, but the complete 14-workspace responsive atlas and
  independent accessibility review remain open.
- G3 requirements: deterministic B0/B1 forecasts, archive/replay, scoring,
  feature cutoffs, walk-forward evidence, diagnostics and registry controls are
  present for synthetic data. They are not validated live performance and still
  require the specified independent assurance/owner gates.
- RIL-069–071: specialist manifests, synthetic ablation metrics and the
  independent-assurance packet are present. They remain synthetic-only and
  explicitly HOLD until independent review and owner decision references exist.
- RIL-060/T-C: the release gate now aggregates local evidence, automated
  validation, visual/accessibility/model review, owner approval, external gates
  and prohibited-capability checks into a hashed report. It cannot authorize
  activation, promotion, wagering or external connectivity.
- G4–G11 requirements: retained as gated future work; external providers,
  production OIDC, production deployment and final pilot approval are not
  claimed.
