# R-AI-cing Nexus project sprint plan

**Plan date:** 2026-10-12  
**Repository:** `birko21/R-AI-cing_Nexus`  
**Active branch:** `codex/phase0-design-rescue`  
**Current PR:** [#177](https://github.com/birko21/R-AI-cing_Nexus/pull/177)  
**Operating mode:** synthetic-only, local-first, read-only, non-wagering

## How to read this plan

This plan covers the imported design-rescue epics E12–E16 and the technical
foundation that must support them. A ticket is not considered complete merely
because code or CI exists. Each ticket must have its required evidence, and
human, rights, legal, accessibility, racing-domain, owner, or security
decisions remain explicit gates.

The plan uses four states:

- **COMPLETE:** implementation and required automated evidence are present.
- **READY:** the engineering package is prepared and is waiting for a named
  human or external decision.
- **IN PROGRESS:** implementation is actively being built.
- **BLOCKED:** progress requires an external dependency that cannot be safely
  simulated or inferred.

No sprint may activate a live provider, use unapproved artwork, add wagering or
staking, weaken authentication, deploy the product, or alter The Long Straight.

## Sprint map

| Sprint | Focus | Tickets | Exit condition |
|---|---|---|---|
| S0 | Recovery, source control and V7 baseline | E12 / NXD-001–005 | Hashes, reference manifest, fixture contract, rights ledger, and quality rubric are versioned; human decisions remain recorded rather than inferred. |
| S1 | Renderer feasibility and Tactical Track proof | E13 / NXD-006–011 | Side-on Tactical Track, equal-scale runners, metadata-driven silks, linked pace map, mobile evidence, and three-code mechanics package are reviewable. |
| S2 | Premium design system and workspace build-out | E14 / NXD-012–017 | Tokens, Dual Atmosphere components, and the seven supporting workspace families are implemented with synthetic/degraded states. |
| S3 | Responsive atlas and end-to-end story | E14–E15 / NXD-018–019 | All 14 workspaces have responsive state evidence and a consistent synthetic research narrative. |
| S4 | Independent assurance and isolation | E15 / NXD-020–023 | Visual, accessibility, racing-domain/model-trust, rights, security, and no-wagering evidence is assembled; missing human decisions keep the release HOLD. |
| S5 | Controlled handover and pilot readiness | E16 / NXD-024–027 | Approved version, exact Codex handover, no-regression dry run, and go/no-go register exist. No approval is manufactured. |
| T-A | Synthetic ingestion and provider-neutral data plane | RIL-011–016, RIL-032, RIL-061–068 | Canonical identity, receipts, replay, quarantine, as-of materialization, synthetic Betfair market lane, and durable job leases are reproducible offline. |
| T-B | Forecasts, model assurance and paper analysis | RIL-021–040, RIL-051–055 | Deterministic baselines, chronological evaluation, diagnostics, paper-only market math, and experimental code-specific modules have replayable evidence. |
| T-C | Operations and release controls | RIL-056–060 | Authentication, supply-chain, observability, backup/restore, retention, performance, and pilot evidence pass their gates. |
| T-D | Approved external sources | RIL-072–076 | **Blocked until written provider rights, credentials, retention, display, model-use, cost, and security approvals exist.** |

## Legacy technical epic alignment

The original RIL-001–060 backlog is executed through the following dependency
ordered technical sprints. “Evidence present” means the local implementation
and automated proof exist; it does not replace a required human, legal,
provider, or production gate.

| Sprint | RIL scope | Current state | Remaining exit gate |
|---|---|---|---|
| T0 | RIL-001–005 governance and evidence | Evidence present | Owner/source confirmation where required |
| T1 | RIL-006–010 local foundation, API, auth | Implementation present | Disposable PostgreSQL apply/rollback smoke |
| T2 | RIL-011–015 domain, provenance, entitlement | Synthetic/offline implementation present | Rights-aware production evidence remains gated |
| T3 | RIL-016–020 synthetic UX and degraded states | Tactical Track and core synthetic UI evidence present | Full 14-workspace atlas and independent accessibility review |
| T4 | RIL-021–025 baselines and forecast archive | Synthetic implementation and replay evidence present | No validated/live claim; owner/model assurance gate |
| T5 | RIL-026–030 backtesting and model assurance | Synthetic feature, walk-forward, metrics and registry evidence present | Independent assurance and promotion decision |
| T6 | RIL-031–035 scraping/provider framework | Provider-neutral framework present | Real source remains blocked by rights/credentials |
| T7 | RIL-036–040 market and paper analysis | Read-only paper-analysis foundation present | Market-workbench completeness and licence-aware export review |
| T8 | RIL-041–045 selections and responsible use | Backend controls and fixtures present | UX/accessibility and owner pilot review |
| T9 | RIL-046–050 research assistant | Bounded tools, citation/egress and offline evaluation evidence present | Provider/model policy approval before activation |
| T10 | RIL-051–055 specialist models and scenarios | Synthetic code-specific modules and scenario evidence present | Independent challenger/model review |
| T11 | RIL-056–060 operations and pilot | Security, backup, retention and release foundations present | Approved OIDC, production operations and owner sign-off |

## Detailed ticket plan

### S0 — Recovery and baseline

| Ticket | Planned outcome | Current handling |
|---|---|---|
| NXD-001 | Immutable V7 source manifest and hashes | Baseline verified; retain as evidence and obtain creative-owner confirmation. |
| NXD-002 | 14-screen reference and feature-retention matrix | Prepare matrix; owner approval required. |
| NXD-003 | Three-code identity and synthetic fixture contract | Synthetic fixture and canonical identity foundations exist; add replay/edge-state coverage. |
| NXD-004 | Asset, rights, and accessibility ledger | Rights-pending ledger exists; legal/owner clearance remains open. |
| NXD-005 | Quality charter, variance rubric, and approval rules | Evidence packet exists; creative/QA acceptance remains open. |

### S1 — Renderer and Tactical Track

| Ticket | Planned outcome | Current handling |
|---|---|---|
| NXD-006 | Renderer feasibility comparison and decision record | Layered 2D proof selected for the lab; record rationale and limits. |
| NXD-007 | Isolated cinematic racecourse backdrop | Side-on synthetic backdrop exists; production rights remain HOLD. |
| NXD-008 | Independent realistic runner layers and code asset rules | Equal-scale synthetic runner layers exist; production asset clearance remains HOLD. |
| NXD-009 | Spatial grouping and honest confidence-band contract | Four-band V7 grouping is implemented; specialist review remains required. |
| NXD-010 | Matched mobile Tactical View and analytical pace map | Next implementation target after the current visual decision gate. |
| NXD-011 | Thoroughbred, harness, and greyhound mechanics review | Requires named independent racing specialists; no approval inferred. |

### S2 — Design system and supporting workspaces

| Ticket | Planned outcome | Current handling |
|---|---|---|
| NXD-012 | Dual Atmosphere tokens and reusable components | Start only after S0 decisions and Tactical Track direction are accepted. |
| NXD-013–017 | Command Centre, Runner, Model Lab, Markets/Evidence, Notebook/Settings | Build from shared tokens and synthetic/degraded-state contracts; each gets its own evidence slice. |

### S3 — Atlas and story conformance

| Ticket | Planned outcome | Current handling |
|---|---|---|
| NXD-018 | Responsive, motion, loading, empty, stale, denied, and restricted atlas for all 14 workspaces | Requires S2 workspace slices and accessibility evidence. |
| NXD-019 | End-to-end synthetic research story with consistent identity | Requires the atlas and fixture conformance tests. |

### S4 — Assurance and isolation

| Ticket | Planned outcome | Current handling |
|---|---|---|
| NXD-020 | Reference-by-reference visual gate | Human creative-owner verdict required. |
| NXD-021 | WCAG 2.2 AA and real-device usability review | Independent accessibility reviewer and device evidence required. |
| NXD-022 | Three-code domain/model-trust review | Independent specialists and model-assurance reviewer required. |
| NXD-023 | Security, rights, no-wagering, and deployed-isolation evidence | Engineering checks can be automated; legal/security acceptance remains human-owned. |

### S5 — Controlled handover

| Ticket | Planned outcome | Current handling |
|---|---|---|
| NXD-024 | Freeze approved release and decision register | Requires S4 decisions and immutable manifest. |
| NXD-025 | Exact Codex master handover and implementation slices | Prepare from the approved release only. |
| NXD-026 | Visual-fidelity/no-regression dry run | Requires approved references and owner comparison. |
| NXD-027 | Go/no-go meeting and retained release gates | Requires owner and independent reviewer decisions. |

## Technical lane

The technical lane can advance while the visual lane is waiting, but it must
remain synthetic-only until T-D approvals exist.

1. **T-A:** finish synthetic fixture replay manifests, capability evidence,
   canonical identity reconciliation, bitemporal/as-of materialization,
   quarantine reports, and PostgreSQL-backed ingestion smoke tests.
2. **T-B:** verify deterministic B0/B1 forecast manifests, leakage defenses,
   walk-forward evaluation, uncertainty/coverage diagnostics, paper-market
   calculations, and experimental three-code modules. The current branch now
   includes a hashed nine-lane specialist manifest covering each code's form,
   market, and combined input contracts.
3. **T-C:** add secret/dependency scans, operational budgets and kill switches,
   backup/restore transcripts, retention deletion tests, and release checklists.
4. **T-D:** do not implement or activate real provider transports until every
   provider-specific rights and security gate is recorded.

## Definition of done for every sprint

- Required implementation exists in the reviewed branch.
- Automated tests execute and their commands/exit codes are recorded.
- Synthetic, licensed, public-scraped, restricted, stale, and unavailable
  states are not collapsed into one another.
- Desktop/tablet/mobile evidence exists for visual changes at 1440×900,
  768×1024, and 390×844.
- Reference names, hashes, rights/design state, variance notes, and unresolved
  risks are attached.
- Human decisions are recorded only by the actual reviewer/owner; CI never
  substitutes for approval.

## Current sprint selection

The active engineering sprint is **T-A: Synthetic ingestion and provider-
neutral data plane**. The current branch contains:

- a synthetic-only ingestion worker;
- idempotent replay, pagination, retry, and quarantine behavior;
- PostgreSQL job leasing and migration 019;
- deterministic synthetic Betfair replay-manifest generation;
- replay-manifest reconciliation that detects checksum/page/count drift;
- typed provider-evidence records with no activation authority;
- strict provider-feature bridge quarantine for timestamp, retention, rights,
  and cutoff failures;
- provider-neutral capability and raw-envelope boundaries; and
- the current API regression suite passing.

The next T-A increment is a local PostgreSQL migration/ingestion smoke test
when a disposable `DATABASE_URL` is provided, followed by broader as-of
reconciliation coverage. The visual sprint remains READY for human review,
not silently advanced.
