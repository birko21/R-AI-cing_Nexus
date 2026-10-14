# Remaining epics and execution register

**Plan date:** 2026-10-12  
**Operating boundary:** synthetic by default; owner-triggered live read-only
capture is prepared but remains disabled until local credentials and named
approval records are configured. No wagering, trading or automatic actions.

This register is the executable remainder after the completed foundation work.
Tickets marked `COMPLETE` have local implementation and automated evidence.
Tickets marked `BLOCKED_EXTERNAL` or `BLOCKED_HUMAN` are prepared, but cannot
be honestly closed without authority or evidence that is not present in this
repository.

## Epic R1 — Engineering completion and release evidence

| Ticket | Outcome | Status | Evidence |
|---|---|---|---|
| R1.1 | Inventory all remaining engineering, provider and review gates. | COMPLETE | This register and `docs/PROJECT_SPRINT_PLAN.md` |
| R1.2 | Exercise the real worker-to-raw-receipt-to-canonical-projection path. | COMPLETE | `scripts/run_postgres_backend_acceptance.py`, PostgreSQL CI |
| R1.3 | Pressure-test replay, tamper detection, projection replay and retries. | COMPLETE | `scripts/pressure_test_synthetic_pipeline.py` |
| R1.4 | Add one machine-readable safe-completion gate aggregating local evidence and external holds. | COMPLETE | `scripts/validate_safe_completion_gate.py`, `docs/evidence/ril-060/safe-completion-gate.json` |

## Epic R2 — Data-science reproducibility and assurance

| Ticket | Outcome | Status | Evidence |
|---|---|---|---|
| R2.1 | Re-run deterministic RIL-061 benchmark artifacts twice and compare hashes. | COMPLETE | `scripts/pressure_test_data_science.py` |
| R2.2 | Re-run B3 LightGBM/CatBoost synthetic artifacts twice across all three codes. | COMPLETE | `docs/evidence/ril-061/b3-synthetic-evaluation.json` |
| R2.3 | Preserve explicit synthetic-only, non-predictive and no-promotion language. | COMPLETE | B3/RIL-061 evidence and assurance fixtures |
| R2.4 | Obtain independent statistical/model-assurance review and owner decision. | BLOCKED_HUMAN | `docs/models/MODEL_ASSURANCE_WORKFLOW.md` |

## Epic R3 — Hosted operations readiness

| Ticket | Outcome | Status | Evidence |
|---|---|---|---|
| R3.1 | Validate the Render Blueprint, OIDC boundary and provider-disabled defaults. | COMPLETE | `scripts/validate_render_blueprint.py`, Render CI |
| R3.2 | Validate migration, lease, replay, downgrade and re-upgrade behavior against disposable PostgreSQL. | COMPLETE | PostgreSQL CI and `docs/evidence/ril-011/postgres-smoke.md` |
| R3.3 | Prepare hosted database/queue/worker topology, telemetry, retention and cost envelope. | BLOCKED_EXTERNAL | `docs/deployment/RENDER_NEXUS_STAGING.md` |
| R3.4 | Apply or deploy the hosted topology and prove real OIDC access. | BLOCKED_EXTERNAL | Requires owner-controlled Render/Auth0 configuration |

## Epic R4 — Approved provider integrations

| Ticket | Outcome | Status | Evidence |
|---|---|---|---|
| R4.1 | Maintain provider-neutral adapter, capability and entitlement contracts. | COMPLETE | `services/api/app/providers.py`, provider evidence fixtures |
| R4.2 | Prepare source-specific decision packs and reconciliation acceptance criteria. | COMPLETE | `docs/provider/` |
| R4.3 | Add secure owner-configured runtime wiring, non-secret status and bounded live capture command. | COMPLETE | `services/api/app/live_provider_runtime.py`, `scripts/run_live_provider_capture.py`, `docs/provider/LIVE_PROVIDER_ACTIVATION.md` |
| R4.4 | Run first owner-controlled connectivity diagnostic without raw retention. | BLOCKED_EXTERNAL | Requires local provider key and two PuntersEdge diagnostic approval records; no key is configured in this workspace |
| R4.5 | Activate retained provider envelopes and provider-specific canonical parsers. | PARTIAL_LOCAL | Generic approved-envelope persistence plus Betfair catalogue parsing/projection are implemented; real response validation, provider form/results parsers and PostgreSQL credentials remain outstanding |
| R4.6 | Validate licensed historical data for walk-forward research. | BLOCKED_EXTERNAL | RIL-077 approval pack and provider export/coverage evidence |

## Epic R5 — Independent assurance and visual review

| Ticket | Outcome | Status | Evidence |
|---|---|---|---|
| R5.1 | Automated browser, axe, contract, security and no-wagering evidence. | COMPLETE | CI matrix and S4 packet |
| R5.2 | Independent accessibility, racing-domain, model-assurance and security-owner decisions. | BLOCKED_HUMAN | S4 review gates |
| R5.3 | Visual-owner comparison of the approved V7 reference set. | BLOCKED_HUMAN / LAST | Deliberately held until executable paths are accepted |

## Epic R6 — Controlled pilot handover

| Ticket | Outcome | Status | Evidence |
|---|---|---|---|
| R6.1 | Produce an immutable release manifest and no-regression checklist. | READY | Existing S4/release-gate artifacts are prepared |
| R6.2 | Record owner-approved restricted pilot scope and go/no-go decision. | BLOCKED_HUMAN | `docs/evidence/ril-060/release-gate-checklist.md` |
| R6.3 | Deploy a public or live-provider pilot. | BLOCKED_EXTERNAL | Explicitly out of scope until R3/R4/R5 gates pass |

## Epic R7 — Backend completion and live-data activation

| Ticket | Outcome | Status | Evidence |
|---|---|---|---|
| BE-011 | Expose non-secret provider runtime readiness. | COMPLETE | `/v1/system/status`, commit `09c8e33` |
| BE-012 | Add dedicated provider-read authorization scope. | COMPLETE | `providers:read`, contract/auth tests |
| BE-013 | Add bounded PuntersEdge aggregate-only probe path. | COMPLETE | `/v1/provider-probes/punters-edge`, commit `f20f877` |
| BE-014 | Prevent raw payload retention/return from diagnostics. | COMPLETE | Diagnostic response contract and negative tests |
| BE-015 | Normalize upstream HTTP/transport/JSON failures. | COMPLETE | Provider transport tests |
| BE-016 | Deploy backend-only staging branch and verify health/logs. | COMPLETE | Render deployment `dep-db7n2qm7bikc73bfbk4g`; health `ok`; no error logs |
| BE-017 | Re-run full backend, contract, lint and repository validation. | COMPLETE | 325 tests, Ruff, repository baseline |
| BE-018 | Configure named provider diagnostic approvals and owner permission. | BLOCKED_EXTERNAL | Render/provider owner action required |
| BE-019 | Execute first approved aggregate-only live diagnostic. | BLOCKED_EXTERNAL | Depends on BE-018 and owner token |
| BE-020 | Capture, validate and persist an approved live response. | BLOCKED_EXTERNAL | Depends on real response, rights and database |
| BE-021 | Reconcile live rows into canonical data with quarantine. | BLOCKED_EXTERNAL | Depends on provider sample and parser evidence |
| BE-022 | Run real-data chronological model evaluation. | BLOCKED_EXTERNAL | Depends on historical/model-use approval and labelled data |
| BE-023 | Provision hosted database/worker/queue and prove recovery. | BLOCKED_EXTERNAL | Render plan/resources not provisioned |
| BE-024 | Issue final non-visual backend release gate. | READY_AFTER_EXTERNAL_GATES | Depends on BE-019–023 and independent reviews |

The detailed eight-hour execution register is in
`docs/backlog/BACKEND_COMPLETION_8H.md`.

## Completion rule

R1–R3 local tickets, R4.1–R4.3 and R5.1 are complete in this branch. The
first real request is now an operator action requiring the owner’s local key
and approval record; this workspace currently has neither configured. The
remaining tickets are not safe to simulate: they require provider responses,
retention/model-use evidence, hosted resources, independent reviewers or
owner approval. No ticket grants activation, wagering, promotion or deployment
authority.
