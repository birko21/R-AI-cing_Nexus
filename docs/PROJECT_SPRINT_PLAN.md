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

### Remaining execution sprints

| Sprint | Tickets | Execution now | Exit gate |
|---|---|---|---|
| T-C.1 | RIL-056–060 | **SAFE FOUNDATION COMPLETE** — security scanning, current SBOM, operations budgets/kill switches, isolated backup/retention evidence, assistant budget controls, egress redaction, and hashed release-gate aggregation are checked in and exercised by CI. | OIDC configuration, production telemetry/billing, restore against an approved environment, owner review, visual/accessibility/model/provider gates remain external or human-owned. |
| T-A.2 | G1 / RIL-011–016, 068 | **SAFE FOUNDATION COMPLETE** — disposable-target preflight, CI-backed PostgreSQL 16 migration/lease/replay smoke, durable synthetic-ingestion runner, ingestion-schema verification, cutoff-boundary coverage, and an end-to-end ingestion-to-forecast proof are checked in. | Hosted worker/database/monitoring deployment and broader owner-approved as-of reconciliation remain gated. |
| T-A.3 | G1 / RIL-011–016, 068 | **SAFE FOUNDATION COMPLETE** — separate durable producer (`--enqueue-only`) and signal-aware PostgreSQL synthetic consumer with one transaction per bounded job, cooperative `SIGTERM`/`SIGINT` drain, finite `--once`/`--max-jobs` verification modes, and replay-to-archive verification are checked in. | Hosted worker/database/monitoring deployment remains an owner-approved Render topology gate. |
| S2.1 | NXD-012–019 | **SAFE ENGINEERING FOUNDATION COMPLETE** — responsive 14-entry workspace atlas, shared code/race/field/model context, synthetic-only degraded-state copy, linked research navigation, and desktop/tablet/mobile browser evidence are checked in. | Named visual-owner, accessibility, racing-domain/model-trust, rights and end-to-end narrative reviews remain HOLD gates. |
| S4.1 | NXD-020–023 | **ASSURANCE PACKET COMPLETE** — machine evidence is mapped into a hashed S4 review packet with explicit pending and external-dependency statuses; no approval or activation authority is inferred. | Creative owner, independent accessibility/domain/model reviewers, security owner, OIDC owner, and rights owner must provide the actual decisions. |
| S4.2 | NXD-021–023 | **NON-VISUAL ENGINEERING PROOF COMPLETE** — the synthetic vertical path, automated browser/axe checks, three-code contracts, model/archive replay, security scan, contract validation, and Render isolation checks pass. | Independent accessibility, racing-domain/model, and security-owner decisions remain required. |
| S4.3 | NXD-020 | **DELIBERATELY LAST** — visual-owner comparison is held until the executable data and safety path is accepted. | Named creative owner must compare the approved reference set and record the verdict. |
| T-B.2 | RIL-021–030, 069–071 | **SAFE FOUNDATION COMPLETE** — deterministic B0/B1 forecast manifests, specialist lanes, ablation report and assurance packet are replayable synthetic artifacts and B0/B1 generation is now CI-checked. | Independent reviewer references, owner decision, approved historical rights and no automatic promotion. |
| T-D.1 | RIL-072–077 | **BLOCKED_EXTERNAL_DEPENDENCY** — prepare decision packs only. | Written provider rights, credentials, retention/model-use/display terms, cost/security approval and an approved historical dataset. |

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
| NXD-003 | Three-code identity and synthetic fixture contract | Canonical identity, replay manifests, three-code edge states, and deterministic B0/B1 fixture derivation are implemented and CI-checked. |
| NXD-004 | Asset, rights, and accessibility ledger | Rights-pending ledger exists; legal/owner clearance remains open. |
| NXD-005 | Quality charter, variance rubric, and approval rules | Evidence packet exists; creative/QA acceptance remains open. |

### S1 — Renderer and Tactical Track

| Ticket | Planned outcome | Current handling |
|---|---|---|
| NXD-006 | Renderer feasibility comparison and decision record | Layered 2D proof selected for the lab; record rationale and limits. |
| NXD-007 | Isolated cinematic racecourse backdrop | Side-on synthetic backdrop exists; production rights remain HOLD. |
| NXD-008 | Independent realistic runner layers and code asset rules | Equal-scale synthetic runner layers exist; production asset clearance remains HOLD. |
| NXD-009 | Spatial grouping and honest confidence-band contract | Four-band V7 grouping is implemented; specialist review remains required. |
| NXD-010 | Matched mobile Tactical View and analytical pace map | Side-on Tactical Track, equal-scale runners, linked analytical pace map, responsive atlas evidence, and shared synthetic context are implemented; visual-owner, accessibility, and racing-domain review remain open. |
| NXD-011 | Thoroughbred, harness, and greyhound mechanics review | Requires named independent racing specialists; no approval inferred. |

### S2 — Design system and supporting workspaces

| Ticket | Planned outcome | Current handling |
|---|---|---|
| NXD-012 | Dual Atmosphere tokens and reusable components | Safe token/component foundation is present in the existing shell and the workspace atlas; design-owner acceptance remains open. |
| NXD-013–017 | Command Centre, Runner, Model Lab, Markets/Evidence, Notebook/Settings | Safe synthetic workspace slices and shared context navigation are present; full product-depth review and named evidence acceptance remain open. |

### S3 — Atlas and story conformance

| Ticket | Planned outcome | Current handling |
|---|---|---|
| NXD-018 | Responsive, motion, loading, empty, stale, denied, and restricted atlas for all 14 workspaces | Safe responsive atlas and axe-checked desktop/tablet/mobile evidence are present; real-device and human accessibility review remain open. |
| NXD-019 | End-to-end synthetic research story with consistent identity | Shared code/race/field/model context and linked workspace navigation are implemented; narrative/domain review remains open. |

### S4 — Assurance and isolation

| Ticket | Planned outcome | Current handling |
|---|---|---|
| NXD-020 | Reference-by-reference visual gate | S4 packet prepared; human creative-owner verdict required. |
| NXD-021 | WCAG 2.2 AA and real-device usability review | S4 packet prepared; independent accessibility reviewer and device evidence required. |
| NXD-022 | Three-code domain/model-trust review | S4 packet prepared; independent specialists and model-assurance reviewer required. |
| NXD-023 | Security, rights, no-wagering, and deployed-isolation evidence | S4 packet maps the automated evidence; legal/security acceptance remains human-owned. |

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
   The deterministic T-B ablation report now compares a baseline with one
   incremental synthetic feature/provider lane and remains explicitly HOLD.
   The model-assurance packet is also present, but has no promotion authority
   and remains HOLD without real independent-review and owner references.
3. **T-C:** add secret/dependency scans, operational budgets and kill switches,
   backup/restore transcripts, retention deletion tests, and release checklists.
   The current increment also adds a hashed, fail-closed release-gate report
   that keeps owner, accessibility, model, OIDC, provider-rights and safety
   decisions separate from automated evidence.
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
- a hashed fail-closed release-gate report with no activation or promotion
  authority; and
- provider-neutral capability and raw-envelope boundaries; and
- the current API regression suite passing.

The T-A PostgreSQL migration/ingestion smoke is now executed in CI against an
isolated disposable PostgreSQL 16 service. It validates the explicit target
guard, migration checksums, ingestion schema, producer/consumer replay path,
and downgrade/re-upgrade cycle without requiring a developer or hosted
database credential. The local PowerShell smoke remains available for a
user-supplied disposable loopback target. The durable producer/consumer
handoff and broader provider as-of quarantine suite are present. The visual
sprint remains READY for human review, not silently advanced.
