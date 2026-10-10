# Ticket register

Each ticket is intended to become one GitHub issue. `P0` is critical foundation, `P1` is core product capability, and `P2` is advanced capability. External or owner approvals are blockers, not reasons to fabricate completion.

## E0 — Governance, scope and evidence

### RIL-001 — Import V1.1 source documents and establish repository baseline

- **Priority/gate:** P0 / G0
- **Depends on:** None
- **Acceptance:** Store the supplied V1.1 prompt and master specification with source/date metadata; create `README_START_HERE.md`; record missing source artifacts; keep the project independent from other applications.
- **Evidence:** Repository tree, source hashes, G0 checkpoint.

### RIL-002 — Create decision register, traceability matrix and risk register

- **Priority/gate:** P0 / G0
- **Depends on:** RIL-001
- **Acceptance:** Map requirements and FRs to tickets/tests; record unresolved product, data, legal, statistical and hosting decisions with owners and defaults.
- **Evidence:** `docs/DECISION_REGISTER.md`, traceability report, risk log.

### RIL-003 — Record architecture, security, data-rights and no-wagering ADRs

- **Priority/gate:** P0 / G0
- **Depends on:** RIL-001
- **Acceptance:** Document modular-monolith boundaries, bitemporal provenance, local auth, scraping policy, entitlement enforcement and the permanent no-wagering boundary.
- **Evidence:** ADR set reviewed against V1.1.

### RIL-004 — Define checkpoint and release-evidence schema

- **Priority/gate:** P0 / G0
- **Depends on:** RIL-002
- **Acceptance:** Define machine-readable and human-readable checkpoint formats containing status, commands, exit codes, tests, data mode, rights, model state, cost and risks; successful results cannot be prefilled.
- **Evidence:** Checkpoint JSON schema and sample `BLOCKED` checkpoint.

### RIL-005 — Establish repository workflow and issue conventions

- **Priority/gate:** P0 / G0
- **Depends on:** RIL-002
- **Acceptance:** Define branch naming, commit format, ticket states, review rules, protected-branch policy and how external blockers are recorded.
- **Evidence:** Contributor workflow and local validation script.

## E1 — Local foundation and contracts

### RIL-006 — Bootstrap reproducible local development environment

- **Priority/gate:** P0 / G1
- **Depends on:** RIL-001, RIL-005
- **Acceptance:** Provide pinned Python/Node dependencies, environment example, one-command local start, fixture seed command and documented PostgreSQL/Playwright prerequisites.
- **Evidence:** Clean-machine or clean-environment bootstrap transcript.

### RIL-007 — Implement OpenAPI MVP contract and shared types

- **Priority/gate:** P0 / G1
- **Depends on:** RIL-002
- **Acceptance:** Version API schemas for health, codes, meetings, races, entries, forecasts, selections and errors; generated or hand-checked client types match server responses.
- **Evidence:** Contract diff, schema tests and generated client check.

### RIL-008 — Implement PostgreSQL schema and Alembic migration foundation

- **Priority/gate:** P0 / G1
- **Depends on:** RIL-007
- **Acceptance:** Apply migrations to a disposable local PostgreSQL database; enforce timezone-aware timestamps, append-only fields where required, indexes and migration checksums.
- **Evidence:** Applied migration log, schema inspection and rollback/forward test.

### RIL-009 — Implement FastAPI application, errors, pagination and health

- **Priority/gate:** P0 / G1
- **Depends on:** RIL-007, RIL-008
- **Acceptance:** Serve typed routes with stable error envelopes, bounded pagination, correlation IDs and minimal unauthenticated health/status endpoints.
- **Evidence:** API integration tests and OpenAPI validation.

### RIL-010 — Implement owner authentication, scopes and fail-closed local auth

- **Priority/gate:** P0 / G1
- **Depends on:** RIL-009
- **Acceptance:** Enforce scopes server-side; permit a development token only on loopback with explicit flags; reject production or external binds without approved OIDC; never commit tokens.
- **Evidence:** Auth matrix, negative tests and bind-mode smoke tests.

## E2 — Domain, provenance and entitlement controls

### RIL-011 — Implement canonical three-code domain model and identifiers

- **Priority/gate:** P0 / G1
- **Depends on:** RIL-008
- **Acceptance:** Model meetings, races, runners, entries, participants, codes and market-selection mappings; prevent cross-code and name-only identity collisions.
- **Evidence:** Contract/property tests and entity dictionary.

### RIL-012 — Implement race lifecycle and append-only revision events

- **Priority/gate:** P0 / G1
- **Depends on:** RIL-011
- **Acceptance:** Support acceptances, final fields, scratchings, reserves, postponements, official results, abandoned races and corrections without destructive mutation.
- **Evidence:** State-transition tests and revision audit rows.

### RIL-013 — Implement bitemporal timestamps and fixed `as_of` queries

- **Priority/gate:** P0 / G1
- **Depends on:** RIL-012
- **Acceptance:** Store source event, published, observed, effective and system-valid times; exclude facts not provably available by cutoff; preserve exact field revisions.
- **Evidence:** Future-leak tests and historical replay comparison.

### RIL-014 — Implement immutable raw envelopes, checksums and quarantine

- **Priority/gate:** P0 / G2
- **Depends on:** RIL-011, RIL-013
- **Acceptance:** Persist source identifiers, payload hash, schema version, retrieval metadata, data mode and licence reference; quarantine invalid or unresolved records with reason codes.
- **Evidence:** Envelope fixtures, checksum tests and quarantine report.

### RIL-015 — Implement entitlement, retention and capability guards

- **Priority/gate:** P0 / G4
- **Depends on:** RIL-014
- **Acceptance:** Reject unapproved storage/display/export/LLM operations; expose `NOT_AVAILABLE` or `NOT_ENTITLED`; support source kill switches and retention expiry.
- **Evidence:** Rights matrix tests, export tests and disabled-source smoke test.

## E3 — Synthetic data and three-code research UX

### RIL-016 — Build deterministic synthetic fixture pack for all codes

- **Priority/gate:** P0 / G3
- **Depends on:** RIL-011, RIL-012
- **Acceptance:** Include fictional meetings, fields, historical runs, sections, scratchings, reserves, quotes, results, corrections and edge cases for thoroughbred, harness and greyhound; watermark every record.
- **Evidence:** Fixture manifest, hashes and seed replay.

### RIL-017 — Build Today/Command Centre with code and status filters

- **Priority/gate:** P0 / G2
- **Depends on:** RIL-016
- **Acceptance:** Navigate all codes, show local time and source age, distinguish no racing/no data/unavailable/demo, and never display a synthetic item as live.
- **Evidence:** Desktop/mobile screenshots and Playwright journey.

### RIL-018 — Build meeting, race and field-revision research views

- **Priority/gate:** P0 / G2
- **Depends on:** RIL-016, RIL-017
- **Acceptance:** Show field state, timestamps, active/scratched/reserve entries, tabs for available evidence, archived forecasts and clear invalidation after revisions.
- **Evidence:** E2E field-revision scenario and accessibility checks.

### RIL-019 — Build runner compare and code-specific research panels

- **Priority/gate:** P1 / G2
- **Depends on:** RIL-018
- **Acceptance:** Compare 2–4 runners with matched units and contexts; show distinct thoroughbred, harness and greyhound panels; missing specialty inputs produce explanations, not invented values.
- **Evidence:** Three-code screenshots and component tests.

### RIL-020 — Build responsive degraded states and end-to-end UX evidence

- **Priority/gate:** P0 / G2
- **Depends on:** RIL-017, RIL-018
- **Acceptance:** Cover loading, empty, stale, unavailable, quarantined, unsupported and auth-denied states; meet keyboard, contrast, touch-target and screen-reader requirements.
- **Evidence:** Playwright journeys, accessibility report and screenshots at mobile/desktop sizes.

## E4 — Deterministic baselines and forecast archive

### RIL-021 — Implement B0 uniform baseline

- **Priority/gate:** P0 / G3
- **Depends on:** RIL-013, RIL-016
- **Acceptance:** Produce `1/n` for every active eligible runner only when the field is valid; abstain on unsupported outcomes; record model/version/mode metadata.
- **Evidence:** Property tests and fixture forecast manifests.

### RIL-022 — Implement explicit code-specific B1 form heuristic

- **Priority/gate:** P0 / G3
- **Depends on:** RIL-013, RIL-016, RIL-021
- **Acceptance:** Define deterministic inputs, smoothing, missingness, code-specific weighting, minimum support and normalization; use only pre-cutoff facts; label as illustrative.
- **Evidence:** Statistical contract, unit tests and fixed-seed replay.

### RIL-023 — Implement probability validation and fair-odds transforms

- **Priority/gate:** P0 / G3
- **Depends on:** RIL-021, RIL-022
- **Acceptance:** Enforce finite non-negative probabilities, field membership and absolute sum error `≤1e-8`; handle `p=0` without division; document log-loss/Brier conventions.
- **Evidence:** Property tests and edge-case report.

### RIL-024 — Implement immutable forecast manifests and archive replay

- **Priority/gate:** P0 / G3
- **Depends on:** RIL-013, RIL-023
- **Acceptance:** Store forecast ID, field revision, cutoff, feature snapshot, model hash, active-runner hash, data mode and diagnostic flags; replays reproduce identical outputs.
- **Evidence:** Manifest hash comparison and replay test.

### RIL-025 — Implement scratchings, abstention and forecast invalidation

- **Priority/gate:** P0 / G3
- **Depends on:** RIL-012, RIL-024
- **Acceptance:** New field revisions create new forecasts only when valid; prior forecasts remain immutable and historically addressable; unsupported/dead-heat/coupled-entry cases abstain or follow documented evaluation rules.
- **Evidence:** Scratching, reserve, dead-heat, coupled-entry and correction tests.

## E5 — Backtesting and model assurance

### RIL-026 — Implement code-specific feature schemas and as-of materialization

- **Priority/gate:** P0 / G5
- **Depends on:** RIL-013, RIL-022
- **Acceptance:** Version common and code-specific features, retain missingness/provenance, and materialize deterministic cutoff snapshots without future aggregates.
- **Evidence:** Feature manifest and leakage injection test.

### RIL-027 — Implement chronological walk-forward splitting

- **Priority/gate:** P0 / G5
- **Depends on:** RIL-026
- **Acceptance:** Split by race/date, isolate training/calibration/final test windows, prevent overlap, and support expanding/rolling evaluation.
- **Evidence:** Split manifest and negative overlap tests.

### RIL-028 — Implement log-loss, Brier, calibration and segment metrics

- **Priority/gate:** P0 / G5
- **Depends on:** RIL-027
- **Acceptance:** Score at race level with declared conventions; report N, time range, code, horizon, model version, missingness and confidence intervals; synthetic results are implementation metrics only.
- **Evidence:** Reference calculations and metric report.

### RIL-029 — Implement uncertainty, coverage and OOD diagnostics

- **Priority/gate:** P1 / G5
- **Depends on:** RIL-026, RIL-028
- **Acceptance:** Separate probability from evidence strength; expose support, missingness, disagreement and OOD warnings; abstain when configured thresholds fail.
- **Evidence:** Diagnostics fixtures and UI/API tests.

### RIL-030 — Implement model registry, championship and independent assurance

- **Priority/gate:** P0 / G6
- **Depends on:** RIL-028, RIL-029
- **Acceptance:** Register immutable model artifacts and evaluations; retain rejected models; prevent automated promotion; expose `INSUFFICIENT EVIDENCE`, `SHADOW`, `HOLD`, `BLOCK` and `CHAMPION` honestly.
- **Evidence:** Registry migrations, assurance checkpoint and leaderboard tests.

## E6 — Public scraping and approved provider adapters

### RIL-031 — Implement controlled public-scraping framework

- **Priority/gate:** P1 / G4
- **Depends on:** RIL-014, RIL-015
- **Acceptance:** Allow only configured public URLs; enforce rate limits, timeouts, user agent, robots/terms policy, retry limits and a kill switch; never bypass authentication, paywalls, CAPTCHAs or anti-bot controls.
- **Evidence:** Mock-site integration tests and blocked-access tests.

### RIL-032 — Implement provider capability and adapter contract

- **Priority/gate:** P0 / G4
- **Depends on:** RIL-014, RIL-015
- **Acceptance:** Adapters report supported codes, fields, timestamps, rights, pagination, quotas and unsupported operations; all records use the common raw envelope.
- **Evidence:** Contract tests and capability matrix.

### RIL-033 — Implement scraped-source provenance, retention and replay

- **Priority/gate:** P1 / G4
- **Depends on:** RIL-031, RIL-032
- **Acceptance:** Store retrieval URL, timestamp, content hash, parser version, source mode `SCRAPED_PUBLIC`, retention status and replay fixture; never call scraped data licensed or official by default.
- **Evidence:** Replay test, provenance view and retention test.

### RIL-034 — Integrate the first approved real source

- **Priority/gate:** P1 / G7
- **Depends on:** RIL-015, RIL-032, RIL-033
- **Acceptance:** Proceed only after written rights, credentials, retention, model-training and display permissions are recorded; reconcile representative meetings/runners/results; otherwise remain `BLOCKED_EXTERNAL_DEPENDENCY`.
- **Evidence:** Signed/recorded entitlement, reconciliation report and source checkpoint.

### RIL-035 — Implement source health, reissues, coverage and kill-switch operations

- **Priority/gate:** P1 / G7
- **Depends on:** RIL-034
- **Acceptance:** Detect schema drift, late revisions, outages, stale data, coverage gaps and quota exhaustion; disable affected capabilities without corrupting historical records.
- **Evidence:** Failure-injection tests and health dashboard.

## E7 — Market workbench and paper analysis

### RIL-036 — Implement market-selection and quote provenance model

- **Priority/gate:** P1 / G8
- **Depends on:** RIL-014, RIL-034
- **Acceptance:** Match quotes to exact runner entries and field revisions; store price type, source timestamps, in-play status, size/liquidity and entitlement reference.
- **Evidence:** Mapping quarantine and quote contract tests.

### RIL-037 — Implement timestamped market snapshots and as-of history

- **Priority/gate:** P1 / G8
- **Depends on:** RIL-036
- **Acceptance:** Reconstruct only quotes available by the forecast cutoff; distinguish delayed, stale, missing and closing prices; never substitute closing prices for earlier decisions.
- **Evidence:** Historical snapshot replay and stale-price tests.

### RIL-038 — Implement implied probability, overround and comparability rules

- **Priority/gate:** P1 / G8
- **Depends on:** RIL-037
- **Acceptance:** Support declared market types, margin normalization and `NOT_COMPARABLE`; handle incomplete fields, scratchings, invalid odds and mismatched timestamps.
- **Evidence:** Reference math tests and API responses.

### RIL-039 — Implement paper-only value and settlement simulation

- **Priority/gate:** P1 / G8
- **Depends on:** RIL-038, RIL-028
- **Acceptance:** Model fees, commission, liquidity, fills, scratches, voids, dead heats, removal factors and exposure assumptions; never place orders or imply guaranteed returns.
- **Evidence:** Settlement fixtures, paper ledger and no-order static scan.

### RIL-040 — Build Market Workbench UI and licence-aware export

- **Priority/gate:** P1 / G8
- **Depends on:** RIL-038, RIL-039
- **Acceptance:** Show source, timestamp, freshness, market type, overround and comparison status; suppress restricted raw prices/exports; display `NOT_COMPARABLE` when gates fail.
- **Evidence:** UI scenarios, export tests and screenshots.

## E8 — Selections, watchlists and responsible use

### RIL-041 — Implement immutable personal selections and deliberate PASS records

- **Priority/gate:** P1 / G3
- **Depends on:** RIL-018, RIL-024
- **Acceptance:** Capture user, decision time, field revision, forecast/quote references, selection type, rationale and `PASS`; corrections use addenda, never mutation.
- **Evidence:** API tests and journal immutability test.

### RIL-042 — Implement official result reconciliation for selections

- **Priority/gate:** P1 / G8
- **Depends on:** RIL-012, RIL-041
- **Acceptance:** Reconcile outcomes only after official results; preserve result corrections; separate user selections, model rankings and paper financial simulations.
- **Evidence:** Result correction and dead-heat outcome tests.

### RIL-043 — Implement stable watchlists and blackbook tracking

- **Priority/gate:** P1 / G8
- **Depends on:** RIL-011, RIL-012
- **Acceptance:** Track stable runner/race identity through name changes, field revisions and source changes; support pause and removal without destroying history.
- **Evidence:** Identity-change integration tests.

### RIL-044 — Implement deduplicated alerts and source-linked change events

- **Priority/gate:** P1 / G8
- **Depends on:** RIL-043, RIL-035
- **Acceptance:** Alert only on confirmed material changes; include source, timestamp, validity, suppression key and cause; prevent duplicate or expired alerts.
- **Evidence:** Event replay, throttle and dedupe tests.

### RIL-045 — Build journal summaries, exports and responsible-use controls

- **Priority/gate:** P1 / G8
- **Depends on:** RIL-041, RIL-042
- **Acceptance:** Report selections vs model forecasts separately; support permitted annotation export, quiet hours, pause, session/time reflection controls and no chase-loss or urgency cues.
- **Evidence:** Summary calculations, export entitlement tests and UX review.

## E9 — Evidence-grounded research assistant

### RIL-046 — Define read-only research tool contracts

- **Priority/gate:** P2 / G9
- **Depends on:** RIL-013, RIL-015, RIL-024
- **Acceptance:** Define bounded tools for races, histories, features, markets, forecasts, backtests and provenance; enforce row limits, ACLs and `as_of` on every tool.
- **Evidence:** Tool schemas and authorization tests.

### RIL-047 — Implement evidence citation and numeric-claim validator

- **Priority/gate:** P2 / G9
- **Depends on:** RIL-046
- **Acceptance:** Require source IDs, model IDs, timestamps and limitations for factual claims; reject unsupported probabilities, currentness claims and source assertions.
- **Evidence:** Validator fixtures and negative tests.

### RIL-048 — Implement prompt-injection, redaction and data-egress controls

- **Priority/gate:** P2 / G9
- **Depends on:** RIL-015, RIL-046
- **Acceptance:** Treat ingested text as untrusted data; redact secrets/PII; block disallowed licensed-data transmission; audit every tool call and response.
- **Evidence:** Injection corpus, redaction tests and egress audit.

### RIL-049 — Build bounded research assistant experience

- **Priority/gate:** P2 / G9
- **Depends on:** RIL-047, RIL-048
- **Acceptance:** Support evidence-grounded questions, explain discrepancies and create user-approved notes only; gracefully state `NOT_AVAILABLE` instead of estimating missing values.
- **Evidence:** UI journeys and citation screenshots.

### RIL-050 — Create assistant evaluation suite and cost controls

- **Priority/gate:** P2 / G9
- **Depends on:** RIL-047, RIL-048
- **Acceptance:** Maintain curated positive/negative/contradiction/injection cases; enforce token, request and spend budgets; default the feature off until rights and provider policy permit it.
- **Evidence:** Evaluation report and budget kill test.

## E10 — Specialist models and scenario studio

### RIL-051 — Implement thoroughbred specialist feature module

- **Priority/gate:** P2 / G10
- **Depends on:** RIL-026, RIL-034
- **Acceptance:** Support documented class, distance, track/going, barrier, weight, pace and sectional features with missingness and provenance; no causal claims from attribution.
- **Evidence:** Feature dictionary and code-specific evaluation.

### RIL-052 — Implement harness specialist feature and position scenarios

- **Priority/gate:** P2 / G10
- **Depends on:** RIL-026, RIL-034
- **Acceptance:** Support start type, row/barrier, pacing, sectionals and running-line hypotheses; label uncalibrated scenarios `EXPERIMENTAL`.
- **Evidence:** Synthetic scenario tests and capability states.

### RIL-053 — Implement greyhound specialist feature and interference module

- **Priority/gate:** P2 / G10
- **Depends on:** RIL-026, RIL-034
- **Acceptance:** Support box, first split, early acceleration, bend/run line, grade, trouble and interference inputs; reserve activation recomputes only authorised features.
- **Evidence:** Greyhound fixture tests and missing-data states.

### RIL-054 — Build reproducible Scenario Studio and simulation engine

- **Priority/gate:** P2 / G10
- **Depends on:** RIL-051, RIL-052, RIL-053
- **Acceptance:** Store assumptions, seed, sample size, inputs, model version and output hash; distinguish observed facts from hypotheses; abstain where calibration is absent.
- **Evidence:** Seed replay, bounds tests and UI screenshots.

### RIL-055 — Evaluate advanced code-specific challengers

- **Priority/gate:** P2 / G10
- **Depends on:** RIL-027, RIL-028, RIL-051, RIL-052, RIL-053
- **Acceptance:** Compare challengers against uniform/form/market baselines on chronological holdouts; no challenger becomes champion without independent assurance and owner approval.
- **Evidence:** Preregistered study, metrics, CIs and promotion decision.

## E11 — Security, operations and pilot release

### RIL-056 — Implement approved OIDC production authentication

- **Priority/gate:** P0 / G11
- **Depends on:** RIL-010
- **Acceptance:** Integrate an approved issuer with signature, issuer, audience, expiry and scope validation; retain the local token only for loopback development; no default production credentials.
- **Evidence:** Auth configuration, negative tests and owner approval.

### RIL-057 — Implement secrets, dependency and supply-chain controls

- **Priority/gate:** P0 / G11
- **Depends on:** RIL-006, RIL-010
- **Acceptance:** Add secret scanning, dependency audit, lockfile review, SBOM where feasible, log redaction and frontend-secret checks; provider keys remain server-side.
- **Evidence:** CI reports and secret absence scan.

### RIL-058 — Implement observability, quotas, costs and provider kill switches

- **Priority/gate:** P0 / G11
- **Depends on:** RIL-015, RIL-035
- **Acceptance:** Track jobs, source health, latency, errors, quotas, estimated AUD spend and model tokens; enforce 50/80/100% alerts and disable noncritical outbound work at cap.
- **Evidence:** Budget simulation and operational dashboard.

### RIL-059 — Implement backup, restore, retention and migration runbooks

- **Priority/gate:** P0 / G11
- **Depends on:** RIL-008, RIL-014, RIL-015
- **Acceptance:** Back up permitted data, restore into an isolated environment, verify hashes/manifests, test migration rollback and delete restricted data according to retention rules.
- **Evidence:** Restore transcript, checksum report and runbook.

### RIL-060 — Complete performance/accessibility hardening and pilot sign-off

- **Priority/gate:** P0/P1 / G11
- **Depends on:** RIL-020, RIL-030, RIL-040, RIL-045, RIL-050, RIL-055, RIL-056–RIL-059
- **Acceptance:** Pass responsive UX, keyboard/screen-reader, controlled p95, security, restore, provenance, no-wagering and degraded-source checks; publish final gate evidence and obtain owner approval for the restricted pilot scope.
- **Evidence:** Release checklist, screenshots, test report, unresolved-risk register and signed owner decision.

